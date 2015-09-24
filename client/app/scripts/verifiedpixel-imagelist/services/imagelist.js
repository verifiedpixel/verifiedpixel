(function() {
    'use strict';

    ImageListService.$inject = ['$location', 'gettext', 'metadata', 'api'];
    function ImageListService($location, gettext, metadata, api) {

        // @TODO: add VppTagService?
        var vppTags;
        this.getTags = function(scope) {
            if (typeof vppTags === 'undefined') {
                metadata.initialize().then(function() {
                    scope.metadata = metadata.values;
                    vppTags = {};
                    metadata.values.vpp_tags.forEach(function(elem) {
                        vppTags[elem.qcode] = elem.name;
                    });
                    scope.vppTags = vppTags;
                });
            } else {
                scope.vppTags = vppTags;
            }
        };
        this.addTag = function(item, tagCode) {
            var item_clone = _.clone(item);
            var tags = item.vpp_tag || [];
            tags.push(tagCode);
            item_clone._links.self.href = item_clone._links.self.href.replace('search/', 'archive/');
            item_clone._links.self.title = 'Archive';
            api('archive').save(item_clone, {'vpp_tag': tags});
        };
        this.removeTag = function(item, tagCode) {
            var item_clone = _.clone(item);
            var tags = item.vpp_tag;
            tags.splice(tags.indexOf(tagCode), 1);
            item_clone._links.self.href = item_clone._links.self.href.replace('search/', 'archive/');
            item_clone._links.self.title = 'Archive';
            api('archive').save(item_clone, {'vpp_tag': tags});
        };

        var sortOptions = [
            {field: 'firstcreated', label: gettext('Created')},
            {field: 'versioncreated', label: gettext('Updated')},
            {field: 'verification.stats.izitru.verdict', label: gettext('Izitru Verdict')},
            {field: 'verification.stats.izitru.location', label: gettext('Izitru Location')},
            {field: 'verification.stats.incandescent.total_google', label: gettext('GRIS Results')},
            {field: 'verification.stats.tineye.total', label: gettext('Tineye Results')},
            {field: 'urgency', label: gettext('News Value')},
            {field: 'anpa_category.name', label: gettext('Category')},
            {field: 'slugline', label: gettext('Keyword')},
            {field: 'priority', label: gettext('Priority')}
        ];

        function getSort() {
            var sort = ($location.search().sort || 'firstcreated:desc').split(':');
            return angular.extend(_.find(sortOptions, {field: sort[0]}), {dir: sort[1]});
        }

        function sort(field) {
            var option = _.find(sortOptions, {field: field});
            setSortSearch(option.field, option.defaultDir || 'desc');
        }

        function toggleSortDir() {
            var sort = getSort();
            var dir = sort.dir === 'asc' ? 'desc' : 'asc';
            setSortSearch(sort.field, dir);
        }

        function setSortSearch(field, dir) {
            $location.search('sort', field + ':' + dir);
            $location.search('page', null);
        }

        /*
         * Function for finding object by string array for subject codes
         */
        this.getSubjectCodes = function (currentTags, subjectcodes) {
            var queryArray = currentTags.selectedParameters, filteredArray = [];
            if (!$location.search().q) {
                return filteredArray;
            }
            for (var i = 0, queryArrayLength = queryArray.length; i < queryArrayLength; i++) {
                var queryArrayElement = queryArray[i];
                if (queryArrayElement.indexOf('subject.name') !== -1) {
                    var elementName = queryArrayElement.substring(
                            queryArrayElement.lastIndexOf('(') + 1,
                            queryArrayElement.lastIndexOf(')')
                            );
                    for (var j = 0, subjectCodesLength = subjectcodes.length; j < subjectCodesLength; j++) {
                        if (subjectcodes[j].name === elementName) {
                            filteredArray.push(subjectcodes[j]);
                        }
                    }
                }
            }
            return filteredArray;
        };

        // sort public api
        this.setSort = sort;
        this.getSort = getSort;
        this.sortOptions = sortOptions;
        this.toggleSortDir = toggleSortDir;

        /**
         * Single query instance
         */
        function Query(params) {
            var DEFAULT_SIZE = 25,
                size,
                filters = [],
                post_filters = [];

            if (params == null) {
                params = {};
            }

            /**
             * Set from/size for given query and params
             *
             * @param {Object} query
             * @param {Object} params
             * @returns {Object}
             */
            function paginate(query, params) {
                var page = params.page || 1;
                var pagesize = size || Number(localStorage.getItem('pagesize')) || Number(params.max_results) || DEFAULT_SIZE;
                query.size = pagesize;
                query.from = (page - 1) * query.size;
            }

            function buildFilters(params, query) {

                if (params.beforefirstcreated || params.afterfirstcreated) {
                    var range = {firstcreated: {}};
                    if (params.beforefirstcreated) {
                        range.firstcreated.lte = params.beforefirstcreated;
                    }

                    if (params.afterfirstcreated) {
                        range.firstcreated.gte = params.afterfirstcreated;
                    }

                    query.post_filter({range: range});
                }

                if (params.beforeversioncreated || params.afterversioncreated) {
                    var vrange = {versioncreated: {}};
                    if (params.beforeversioncreated) {
                        vrange.versioncreated.lte = params.beforeversioncreated;
                    }

                    if (params.afterversioncreated) {
                        vrange.versioncreated.gte = params.afterversioncreated;
                    }

                    query.post_filter({range: vrange});
                }

                if (params.after)
                {
                    var facetrange = {firstcreated: {}};
                    facetrange.firstcreated.gte = params.after;
                    query.post_filter({range: facetrange});
                }

                if (params.type) {
                    var type = {
                        type: JSON.parse(params.type)
                    };
                    query.post_filter({terms: type});
                } else {
                    // default to only picture types
                    query.post_filter({terms: {type: ['picture']}});
                }

                if (params.urgency) {
                    query.post_filter({terms: {urgency: JSON.parse(params.urgency)}});
                }

                if (params.source) {
                    query.post_filter({terms: {source: JSON.parse(params.source)}});
                }

                if (params.category) {
                    query.post_filter({terms: {'anpa_category.name': JSON.parse(params.category)}});
                }

                if (params.desk) {
                    query.post_filter({terms: {'task.desk': JSON.parse(params.desk)}});
                } else {
                    // default desk to verified images
                    // TODO: lookup desk by name here
                    //query.post_filter({terms: {'task.desk': ['55b0b4c788f929738fa5d069']}});
                }

                if (params.stage) {
                    query.post_filter({terms: {'task.stage': JSON.parse(params.stage)}});
                }

                if (params.state) {
                    query.post_filter({terms: {'state': JSON.parse(params.state)}});
                }

                // add filemeta and verification filters
                if (params.make) {
                    query.post_filter({terms: {'filemeta.Make': JSON.parse(params.make)}});
                }
                if (params.capture_location) {
                    query.post_filter({terms: {'verification.stats.izitru.location': JSON.parse(params.capture_location)}});
                }
                if (params.izitru) {
                    query.post_filter({terms: {'verification.stats.izitru.verdict': JSON.parse(params.izitru)}});
                }
                if (params.vpp_tag) {
                    query.post_filter({terms: {'vpp_tag': JSON.parse(params.vpp_tag)}});
                }
                if (params.original_source) {
                    query.post_filter({terms: {'original_source': JSON.parse(params.original_source)}});
                }
            }

            /**
             * Get criteria for given query
             */
            this.getCriteria = function getCriteria(withSource) {
                var search = params;
                var sort = getSort();
                var criteria = {
                    query: {filtered: {filter: {and: filters}}},
                    sort: [_.zipObject([sort.field], [sort.dir])]
                };

                if (post_filters.length > 0) {
                    criteria.post_filter = {'and': post_filters};
                }

                paginate(criteria, search);

                if (search.q) {
                    criteria.query.filtered.query = {query_string: {
                        query: search.q,
                        lenient: false,
                        default_operator: 'AND'
                    }};
                }

                if (withSource) {
                    criteria = {source: criteria};
                    if (search.repo) {
                        criteria.repo = search.repo;
                    }
                }

                return criteria;
            };

            /**
             * Add filter to query
             *
             * @param {Object} filter
             */
            this.filter = function addFilter(filter) {
                filters.push(filter);
                return this;
            };

            this.post_filter = function addPostFilter(filter) {
                post_filters.push(filter);
                return this;
            };

            /**
             * Set size
             *
             * @param {number} _size
             */
            this.size = function setSize(_size) {
                size = _size != null ? _size : size;
                return this;
            };

            // do base filtering
            if (params.spike) {
                this.filter({term: {state: 'spiked'}});
            } else {
                this.filter({not: {term: {state: 'spiked'}}});
            }

            buildFilters(params, this);
        }

        /**
         * Start creating a new query
         *
         * @param {Object} params
         */
        this.query = function createQuery(params) {
            return new Query(params);
        };

        this.markViewed = function(item) {
            if (item && !item.viewed) {
                var item_clone = _.clone(item);
                item_clone._links.self.href = item_clone._links.self.href.replace('search/', 'archive/');
                item_clone._links.self.title = 'Archive';
                api('archive').save(item_clone, {'viewed': true});
                item.viewed = true;
            }
        };

        /**
         * Reorient specified element.
         *
         * @param {number} orientation
         * @param {object} element
         * @returns {undefined}
         */
            this.reOrient = function reOrient(orientation, element) {
                // reset css first
                element.css({
                    '-moz-transform': 'none',
                    '-o-transform': 'none',
                    '-webkit-transform': 'none',
                    'transform': 'none',
                    'filter': 'none',
                    '-ms-filter': 'none'
                });
                switch (orientation) {
                    case 1:
                        // No action needed
                        break;
                    case 2:
                        element.css({
                            '-moz-transform': 'scaleX(-1)',
                            '-o-transform': 'scaleX(-1)',
                            '-webkit-transform': 'scaleX(-1)',
                            'transform': 'scaleX(-1)',
                            'filter': 'FlipH',
                            '-ms-filter': 'FlipH'
                        });
                        break;
                    case 3:
                        element.css({
                            'transform': 'rotate(180deg)'
                        });
                        break;
                    case 4:
                        element.css({
                            '-moz-transform': 'scaleX(-1)',
                            '-o-transform': 'scaleX(-1)',
                            '-webkit-transform': 'scaleX(-1)',
                            'transform': 'scaleX(-1) rotate(180deg)',
                            'filter': 'FlipH',
                            '-ms-filter': 'FlipH'
                        });
                        break;
                    case 5:
                        element.css({
                            '-moz-transform': 'scaleX(-1)',
                            '-o-transform': 'scaleX(-1)',
                            '-webkit-transform': 'scaleX(-1)',
                            'transform': 'scaleX(-1) rotate(90deg)',
                            'filter': 'FlipH',
                            '-ms-filter': 'FlipH'
                        });
                        if (element.hasClass('vpp-selected-preview')) {
                            element.css({
                                'margin-top': '115px'
                            });
                        }
                        break;
                    case 6:
                        element.css({
                            'transform': 'rotate(90deg)'
                        });
                        if (element.hasClass('vpp-selected-preview')) {
                            element.css({
                                'margin-top': '115px'
                            });
                        }
                        break;
                    case 7:
                        element.css({
                            '-moz-transform': 'scaleX(-1)',
                            '-o-transform': 'scaleX(-1)',
                            '-webkit-transform': 'scaleX(-1)',
                            'transform': 'scaleX(-1) rotate(-90deg)',
                            'filter': 'FlipH',
                            '-ms-filter': 'FlipH'
                        });
                        if (element.hasClass('vpp-selected-preview')) {
                            element.css({
                                'margin-top': '115px'
                            });
                        }
                        break;
                    case 8:
                        element.css({
                            'transform': 'rotate(-90deg)'
                        });
                        if (element.hasClass('vpp-selected-preview')) {
                            element.css({
                                'margin-top': '115px'
                            });
                        }
                        break;
                }
            }; // end reOrient

        /**
         * Functions for formatting EXIF data
         */
        function GPSArrayToFloat(input, ref){
            var d0 = input[0][0];
            var d1 = input[0][1];
            var d = (d0 / d1);

            var m0 = input[1][0];
            var m1 = input[1][1];
            var m = (m0 / m1);

            var s0 = input[2][0];
            var s1 = input[2][1];
            var s = (s0 / s1);
            var value = (d + (m / 60) + (s / 3600));

            if ((ref === 'S') || (ref === 'W')) {
                value = 0 - value;
            }
            return value;
        }

        this.convertExif = function convertExif(filemetaLowered, filemetaConverted) {
            var filemeta = (filemetaLowered) ? filemetaLowered : {};
            var converted = (filemetaConverted) ? filemetaConverted : {};
            // check to see if the file latitude record exists before
            // trying to return anything // longitude is there for the sake of completeness
            if (filemeta.gpsinfo){
                if (filemeta.gpsinfo.gpslatitude && filemeta.gpsinfo.gpslongitude) {
                    // lat is always first
                    converted.gpslat = GPSArrayToFloat(
                        filemeta.gpsinfo.gpslatitude,
                        filemeta.gpsinfo.gpslatituderef
                    );
                    converted.gpslon = GPSArrayToFloat(
                        filemeta.gpsinfo.gpslongitude,
                        filemeta.gpsinfo.gpslongituderef
                    );
                }
                if (filemeta.gpsinfo.gpsimgdirection) {
                    converted.gpsdirection = (
                        filemeta.gpsinfo.gpsimgdirection[0] /
                        filemeta.gpsinfo.gpsimgdirection[1]
                    ).toFixed(3);
                    converted.markerdirection = Math.ceil(converted.gpsdirection / 10) * 10;
                    if (filemeta.lensmodel && filemeta.lensmodel.match(/front/i)) {
                        converted.markerdirection = (converted.markerdirection + 180) % 360;
                    }
                    converted.gpsicon = {
                        url: '/images/gpsdirection/view-' + converted.markerdirection + '.png',
                        size: new google.maps.Size(100, 100),
                        origin: new google.maps.Point(0,0),
                        anchor: new google.maps.Point(50, 50)
                    };
                }
                if (filemeta.gpsinfo.gpsaltitude) {
                    converted.gpsaltitude = filemeta.gpsinfo.gpsaltitude[0] /
                        filemeta.gpsinfo.gpsaltitude[1];
                }
                if (filemeta.gpsinfo.gpsspeed) {
                    converted.gpsspeed = filemeta.gpsinfo.gpsspeed[0] /
                        filemeta.gpsinfo.gpsspeed[1];
                }
                if (filemeta.gpsinfo.gpstrack) {
                    converted.gpstrack = filemeta.gpsinfo.gpstrack[0] /
                        filemeta.gpsinfo.gpstrack[1];
                }
            }

            if (filemeta.aperturevalue) {
                converted.aperture = (
                    filemeta.aperturevalue[0] /
                    filemeta.aperturevalue[1]
                ).toFixed(1);
            }
            if (filemeta.exposuretime) {
                converted.exposuretime = (
                    filemeta.exposuretime[0] /
                    filemeta.exposuretime[1]
                ).toFixed(5);
            }
            if (filemeta.focallength) {
                converted.focallength = (
                    filemeta.focallength[0] /
                    filemeta.focallength[1]
                ).toFixed(2);
            }
            if (filemeta.exposuremode > -1) {
                switch(filemeta.exposuremode) {
                    case 0:
                        converted.exposuremode = 'Not defined';
                        break;
                    case 1:
                        converted.exposuremode = 'Manual';
                        break;
                    case 2:
                        converted.exposuremode = 'Normal program';
                        break;
                    case 3:
                        converted.exposuremode = 'Aperture priority';
                        break;
                    case 4:
                        converted.exposuremode = 'Shutter priority';
                        break;
                    case 5:
                        converted.exposuremode = 'Creative program';
                        break;
                    case 6:
                        converted.exposuremode = 'Action program';
                        break;
                    case 7:
                        converted.exposuremode = 'Portrait mode';
                        break;
                    case 8:
                        converted.exposuremode = 'Landscape mode';
                        break;
                }
            }

            if (filemeta.datetimeoriginal) {
                var dateTimeParts = filemeta.datetimeoriginal.split(' ');
                var dateParts = dateTimeParts[0].split(':');
                var year = dateParts[0];
                var month = dateParts[1];
                var day = dateParts[2];
                var timeParts = dateTimeParts[1].split(':');
                var hour = timeParts[0];
                var min = timeParts[1];
                var sec = timeParts[2];
                var dateString = year+'-'+month+'-'+day+' '+hour+':'+min+':'+ sec;
                converted.datecaptured = new Date(dateString);
            } else {
                converted.datecaptured = 'unknown';
            }

            return converted;
        }

    }


    angular.module('verifiedpixel.imagelist')
        .service('imagelist', ImageListService);
})();
