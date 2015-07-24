(function() {
    'use strict';

    ImageListService.$inject = ['$location', 'gettext'];
    function ImageListService($location, gettext) {
        var sortOptions = [
            {field: 'versioncreated', label: gettext('Updated')},
            {field: 'firstcreated', label: gettext('Created')},
            {field: 'urgency', label: gettext('News Value')},
            {field: 'anpa_category.name', label: gettext('Category')},
            {field: 'slugline', label: gettext('Keyword')},
            {field: 'priority', label: gettext('Priority')}
        ];

        function getSort() {
            var sort = ($location.search().sort || 'versioncreated:desc').split(':');
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
                }

                if (params.stage) {
                    query.post_filter({terms: {'task.stage': JSON.parse(params.stage)}});
                }

                if (params.state) {
                    query.post_filter({terms: {'state': JSON.parse(params.state)}});
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
    }

    TagService.$inject = ['$location', 'desks'];
    function TagService($location, desks) {
        var tags = {};
        tags.selectedFacets = {};
        tags.selectedParameters = [];
        tags.selectedKeywords = [];
        tags.currentSearch = {};

        var FacetKeys = {
            'type': 1,
            'category': 1,
            'urgency': 1,
            'source': 1,
            'day': 1,
            'week': 1,
            'month': 1,
            'desk': 1,
            'stage':1,
            'state':1
        };

        function initSelectedParameters (parameters) {
            tags.selectedParameters = [];
            while (parameters.indexOf(':') > 0 &&
                   parameters.indexOf(':') < parameters.indexOf('(') &&
                   parameters.indexOf(':') < parameters.indexOf(')')) {

                var colonIndex = parameters.indexOf(':');
                var parameter = parameters.substring(parameters.lastIndexOf(' ', colonIndex), parameters.indexOf(')', colonIndex) + 1);
                tags.selectedParameters.push(parameter);
                parameters = parameters.replace(parameter, '');
            }

            return parameters;
        }

        function initSelectedKeywords (keywords) {
            tags.selectedKeywords = [];
            while (keywords.indexOf('(') >= 0) {
                var paranthesisIndex = keywords.indexOf('(');
                var keyword = keywords.substring(paranthesisIndex, keywords.indexOf(')', paranthesisIndex) + 1);
                tags.selectedKeywords.push(keyword);
                keywords = keywords.replace(keyword, '');
            }
        }

        function removeFacet (type, key) {
            if (key.indexOf('Last') >= 0) {
                removeDateFacet();
            } else {
                var search = $location.search();
                if (search[type]) {
                    var keys = JSON.parse(search[type]);
                    keys.splice(keys.indexOf(key), 1);
                    if (keys.length > 0)
                    {
                        $location.search(type, JSON.stringify(keys));
                    } else {
                        $location.search(type, null);
                    }
                }
            }
        }

        function removeDateFacet () {
            var search = $location.search();
            if (search.after) {
                $location.search('after', null);
            }
        }

        function initSelectedFacets () {
            return desks.initialize().then(function(result) {
                tags.selectedFacets = {};
                tags.selectedParameters = [];
                tags.selectedKeywords = [];

                tags.currentSearch = $location.search();

                var parameters = tags.currentSearch.q;
                if (parameters) {
                    var keywords = initSelectedParameters(parameters);
                    initSelectedKeywords(keywords);
                }

                _.forEach(tags.currentSearch, function(type, key) {
                    if (key !== 'q') {
                        tags.selectedFacets[key] = [];

                        if (key === 'desk') {
                            var selectedDesks = JSON.parse(type);
                            _.forEach(selectedDesks, function(selectedDesk) {
                                tags.selectedFacets[key].push(desks.deskLookup[selectedDesk].name);
                            });
                        } else if (key === 'stage') {
                            var stageid = type;
                            _.forEach(desks.deskStages[desks.getCurrentDeskId()], function(deskStage) {
                                if (deskStage._id === JSON.parse(stageid)[0]) {
                                    tags.selectedFacets[key].push(deskStage.name);
                                }
                            });
                        } else if (key === 'after') {

                            if (type === 'now-24H') {
                                tags.selectedFacets.date = ['Last Day'];
                            } else if (type === 'now-1w'){
                                tags.selectedFacets.date = ['Last Week'];
                            } else if (type === 'now-1M'){
                                tags.selectedFacets.date = ['Last Month'];
                            }

                        } else if (FacetKeys[key]) {
                            tags.selectedFacets[key] = JSON.parse(type);
                        }
                    }
                });

                return tags;
            });
        }

        return {
            initSelectedFacets: initSelectedFacets,
            removeFacet: removeFacet
        };
    }

    ImageListController.$inject = ['$scope', '$location', 'api', 'search', 'notify', 'session'];
    function ImageListController($scope, $location, api, search, notify, session) {
        $scope.context = 'search';
        $scope.$on('item:deleted:archive:text', itemDelete);

        function itemDelete(e, data) {
            if (session.identity._id === data.user) {
                refresh();
            }
        }

        $scope.repo = {
            ingest: true,
            archive: true,
            text_archive: true,
            published: true
        };

        function refresh() {
            var query = _.omit($location.search(), '_id');
            if (!_.isEqual(_.omit(query, 'page'), _.omit(oldQuery, 'page'))) {
                $location.search('page', null);
            }

            var criteria = search.query($location.search()).getCriteria(true);
            var provider = 'search';
            if (criteria.repo) {
                provider = criteria.repo;
            }

            if ($scope.repo.search) {
                if ($scope.repo.search !== 'local') {
                    provider = $scope.repo.search;
                } else if (criteria.repo.indexOf(',') >= 0) {
                    provider = 'search';
                }
            }

            api.query(provider, criteria).then(function(result) {
                $scope.items = result;
            });

            oldQuery =  query;
        }

        var oldQuery = _.omit($location.search(), '_id');
        $scope.$watch(function getSearchParams() {
            return _.omit($location.search(), '_id');
        }, refresh, true);
    }

    angular.module('verifiedpixel.imagelist', [
        'ngMap',
        'superdesk.api',
        'superdesk.desks',
        'superdesk.activity',
        'superdesk.list',
        'superdesk.keyboard'
    ])
        .service('search', ImageListService)
        .service('tags', TagService)
        .controller('MultiActionBar', MultiActionBarController)
        .filter('FacetLabels', function() {
            return function(input) {
                if (input.toUpperCase() === 'URGENCY') {
                    return 'News Value';
                } else {
                    return input;
                }

            };
        })
        /**
         * Item filters sidebar
         */
        .directive('vpSearchFacets', ['$location', 'desks', 'privileges', 'tags', 'asset',
            function($location, desks, privileges, tags, asset) {
            desks.initialize();
            return {
                require: '^vpSearchContainer',
                templateUrl: 'scripts/verifiedpixel-imagelist/views/search-facets.html',
                scope: {
                    items: '=',
                    desk: '=',
                    repo: '=',
                    context: '='
                },
                link: function(scope, element, attrs, controller) {
                    scope.flags = controller.flags;
                    scope.sTab = true;
                    scope.aggregations = {};
                    scope.privileges = privileges.privileges;

                    var initAggregations = function () {
                        scope.aggregations = {
                            'type': {},
                            'desk': {},
                            'stage': {},
                            'date': {},
                            'source': {},
                            'category': {},
                            'urgency': {},
                            'state':{}
                        };
                    };

                    scope.$watch('items', function() {

                        initAggregations();
                        tags.initSelectedFacets().then(function(currentTags) {

                            scope.tags = currentTags;

                            if (scope.items && scope.items._aggregations !== undefined) {

                                _.forEach(scope.items._aggregations.type.buckets, function(type) {
                                    scope.aggregations.type[type.key] = type.doc_count;
                                });

                                _.forEach(scope.items._aggregations.category.buckets, function(cat) {
                                    if (cat.key !== '') {
                                        scope.aggregations.category[cat.key] = cat.doc_count;
                                    }
                                });

                                _.forEach(scope.items._aggregations.urgency.buckets, function(urgency) {
                                    scope.aggregations.urgency[urgency.key] = urgency.doc_count;
                                });

                                _.forEach(scope.items._aggregations.source.buckets, function(source) {
                                    scope.aggregations.source[source.key] = source.doc_count;
                                });

                                _.forEach(scope.items._aggregations.state.buckets, function(state) {
                                    scope.aggregations.state[state.key] = state.doc_count;
                                });

                                _.forEach(scope.items._aggregations.day.buckets, function(day) {
                                    scope.aggregations.date['Last Day'] = day.doc_count;
                                });

                                _.forEach(scope.items._aggregations.week.buckets, function(week) {
                                    scope.aggregations.date['Last Week'] = week.doc_count;
                                });

                                _.forEach(scope.items._aggregations.month.buckets, function(month) {
                                    scope.aggregations.date['Last Month'] = month.doc_count;
                                });

                                if (!scope.desk) {
                                    _.forEach(scope.items._aggregations.desk.buckets, function(desk) {
                                        scope.aggregations.desk[desks.deskLookup[desk.key].name] = {
                                                count: desk.doc_count,
                                                id: desk.key
                                            };
                                    }) ;
                                }

                                if (scope.desk) {
                                    _.forEach(scope.items._aggregations.stage.buckets, function(stage) {
                                        _.forEach(desks.deskStages[scope.desk._id], function(deskStage) {
                                            if (deskStage._id === stage.key) {
                                                scope.aggregations.stage[deskStage.name] = {count: stage.doc_count, id: stage.key};
                                            }
                                        });
                                    });
                                }
                            }
                        });
                    });

                    scope.toggleFilter = function(type, key) {
                        if (scope.hasFilter(type, key)) {
                            scope.removeFilter(type, key);
                        } else {
                            if (type === 'date') {
                                scope.setDateFilter(key);
                            } else {
                                scope.setFilter(type, key);
                            }
                        }
                    };

                    scope.removeFilter = function(type, key) {
                        tags.removeFacet(type, key);
                    };

                    scope.setFilter = function(type, key) {
                        if (!scope.isEmpty(type) && key) {
                            var currentKeys = $location.search()[type];
                            if (currentKeys) {
                                currentKeys = JSON.parse(currentKeys);
                                currentKeys.push(key);
                                $location.search(type, JSON.stringify(currentKeys));
                            } else {
                                $location.search(type, JSON.stringify([key]));
                            }
                        } else {
                            $location.search(type, null);
                        }
                    };

                    scope.setDateFilter = function(key) {
                        if (key === 'Last Day') {
                            $location.search('after', 'now-24H');
                        } else if (key === 'Last Week'){
                            $location.search('after', 'now-1w');
                        } else if (key === 'Last Month'){
                            $location.search('after', 'now-1M');
                        } else {
                            $location.search('after', null);
                        }
                    };

                    scope.isEmpty = function(type) {
                        return _.isEmpty(scope.aggregations[type]);
                    };

                    scope.format = function (date) {
                        return date ? moment(date).format('YYYY-MM-DD') : null; // jshint ignore:line
                    };

                    scope.hasFilter = function(type, key) {
                        if (type === 'desk') {
                            return scope.tags.selectedFacets[type] &&
                            scope.tags.selectedFacets[type].indexOf(desks.deskLookup[key].name) >= 0;
                        }

                        return scope.tags.selectedFacets[type] && scope.tags.selectedFacets[type].indexOf(key) >= 0;
                    };
                }
            };
        }])

        .directive('vpSearchTags', ['$location', '$route', 'tags', 'asset', 'metadata',
            function($location, $route, tags, asset, metadata) {
            return {
                scope: {},
                templateUrl: 'scripts/verifiedpixel-imagelist/views/search-tags.html',
                link: function(scope, elem) {

                    tags.initSelectedFacets().then(function(currentTags) {
                        scope.tags = currentTags;
                    });

                    scope.removeFilter = function(type, key) {
                        tags.removeFacet(type, key);
                    };

                    scope.removeParameter = function(param) {
                        var params = $location.search();
                        if (params.q) {
                            params.q = params.q.replace(param, '').trim();
                            $location.search('q', params.q || null);
                            // If it is subject code, remove it from left bar, too
                            if (param.indexOf('subject.name:') !== -1) {
                                var elementName = param.substring(
                                    param.lastIndexOf('(') + 1,
                                    param.lastIndexOf(')')
                                );

                                metadata.removeSubjectTerm(elementName);
                            }
                        }
                    };
                }
            };
        }])

        /**
         * Item list with sidebar preview
         */
        .directive('vpSearchResults', ['$location', 'preferencesService', 'packages', 'tags', 'asset',
            function($location, preferencesService, packages, tags, asset) {
            var update = {
                'archive:view': {
                    'allowed': [
                        'mgrid',
                        'compact'
                    ],
                    'category': 'archive',
                    'view': 'mgrid',
                    'default': 'mgrid',
                    'label': 'Users archive view format',
                    'type': 'string'
                }
            };

            return {
                require: '^vpSearchContainer',
                templateUrl: 'scripts/verifiedpixel-imagelist/views/search-results.html',
                link: function(scope, elem, attr, controller) {

                    var GRID_VIEW = 'mgrid',
                        LIST_VIEW = 'compact';

                    var multiSelectable = (attr.multiSelectable === undefined) ? false : true;

                    scope.flags = controller.flags;
                    scope.selected = scope.selected || {};

                    scope.preview = function preview(item) {
                        if (multiSelectable) {
                            if (_.findIndex(scope.selectedList, {_id: item._id}) === -1) {
                                scope.selectedList.push(item);
                            } else {
                                _.remove(scope.selectedList, {_id: item._id});
                            }
                        }
                        scope.selected.preview = item;
                        $location.search('_id', item ? item._id : null);
                    };

                    scope.openLightbox = function openLightbox() {
                        scope.selected.view = scope.selected.preview;
                    };

                    scope.closeLightbox = function closeLightbox() {
                        scope.selected.view = null;
                    };

                    scope.openSingleItem = function (packageItem) {
                        packages.fetchItem(packageItem).then(function(item) {
                            scope.selected.view = item;
                        });
                    };

                    scope.setview = setView;

                    var savedView;
                    preferencesService.get('archive:view').then(function(result) {
                        savedView = result.view;
                        scope.view = (!!savedView && savedView !== 'undefined') ? savedView : 'mgrid';
                    });

                    scope.$on('key:v', toggleView);

                    function setView(view) {
                        scope.view = view || 'mgrid';
                        update['archive:view'].view = view || 'mgrid';
                        preferencesService.update(update, 'archive:view');
                    }

                    function toggleView() {
                        var nextView = scope.view === LIST_VIEW ? GRID_VIEW : LIST_VIEW;
                        return setView(nextView);
                    }
                }
            };
        }])

        .directive('vpSearchWithin', ['$location', 'asset', function($location, asset) {
            return {
                scope: {},
                templateUrl: 'scripts/verifiedpixel-imagelist/views/search-within.html',
                link: function(scope, elem) {
                    scope.searchWithin = function() {
                        if (scope.within) {
                            var params = $location.search();
                            if (params.q) {
                                scope.query = params.q + ' (' + scope.within + ') ';
                            } else {
                                scope.query = '(' + scope.within + ')';
                            }
                            $location.search('q', scope.query || null);
                            scope.within = null;
                        }
                    };
                }
            };
        }])

        .directive('vpItemContainer', ['$filter', 'desks', 'api', function($filter, desks, api) {
            return {
                scope: {
                    item: '='
                },
                template: '{{item.container}}',
                link: function(scope, elem) {

                    if (scope.item._type !== 'ingest') {
                        if (scope.item.task && scope.item.task.desk) {
                            desks.initialize().then(function() {
                                if (desks.deskLookup[scope.item.task.desk]) {
                                    scope.item.container = 'desk:' + desks.deskLookup[scope.item.task.desk].name ;
                                }
                            });
                        } else {
                            if (scope.item._type === 'archive') {
                                scope.item.container = 'location:workspace';
                            } else {
                                if (scope.item._type === 'text_archive') {
                                    scope.item.container = 'text archive';
                                }
                            }
                        }
                    }
                }
            };
        }])

        .directive('vpItemPreview', ['asset', function(asset) {
            return {
                templateUrl: 'scripts/verifiedpixel-imagelist/views/item-preview.html',
                scope: {
                    item: '=',
                    close: '&',
                    openLightbox: '=',
                    openSingleItem: '='
                },
                link: function(scope) {
                    scope.tab = 'content';
                    scope.$watch('item', function(item) {
                        scope.selected = {preview: item || null};
                    });
                }
            };
        }])

        /**
         * Open Item dialog
         */
        .directive('vpItemGlobalsearch', ['superdesk', 'session', '$location', 'search', 'api', 'notify',
            'gettext', 'keyboardManager', 'asset',
            function(superdesk, session, $location, search, api, notify, gettext, keyboardManager, asset) {
            return {
                scope: {repo: '=', context: '='},
                templateUrl: 'scripts/verifiedpixel-imagelist/views/item-globalsearch.html',
                link: function(scope, elem) {

                    var ENTER = 13;
                    var ESC = 27;
                    scope.meta = {};
                    scope.flags = {enabled: false};
                    var opt = {global: true};
                    keyboardManager.bind('ctrl+0', function() {
                        scope.flags.enabled = true;
                    }, opt);
                    keyboardManager.bind('esc', function() {
                        scope.flags.enabled = false;
                    }, opt);

                    function reset() {
                        scope.meta.unique_name = '';
                    }

                    function openItem(items) {
                        if (items.length > 0) {
                            reset();
                            scope.flags.enabled = false;
                            if (items[0].type === 'composite') {
                                superdesk.intent('author', 'package', items[0]);
                            } else {
                                superdesk.intent('author', 'article', items[0]);
                            }
                        } else {
                            notify.error(gettext('Item not found...'));
                            scope.flags.enabled = true;
                        }
                    }
                    function searchUserContent(criteria) {
                        var resource = api('user_content', session.identity);
                        resource.query(criteria).then(function(result) {
                            openItem(result._items);
                        }, function(response) {
                            scope.message = gettext('There was a problem, item can not open.');
                        });
                    }
                    function fetchItem() {
                        var filter = [
                            {not: {term: {state: 'spiked'}}},
                            {term: {unique_name: scope.meta.unique_name}}
                        ];
                        var criteria = {
                            repo: 'ingest,archive,text_archive,published',
                            source: {
                                query: {filtered: {filter: {
                                    and: filter
                                }}}
                            }
                        };
                        api.query('search', criteria).then(function(result) {
                            scope.items = result._items;
                            if (scope.items.length > 0) {
                                openItem(scope.items);
                                reset();
                            } else {
                                searchUserContent(criteria);
                            }
                        }, function(response) {
                            scope.message = gettext('There was a problem, item can not open.');
                        });
                    }

                    scope.search = function() {
                        fetchItem();
                    };
                    scope.openOnEnter = function($event) {
                        if ($event.keyCode === ENTER) {
                            scope.search();
                            $event.stopPropagation();
                        }
                        if ($event.keyCode === ESC) {
                            _closeDialog();
                        }
                    };

                    scope.close = function() {
                        _closeDialog();
                    };

                    function _closeDialog() {
                        reset();
                        scope.flags.enabled = false;
                    }
                }
            };
        }])
        /**
         * Item search component
         */
        .directive('vpItemSearchbar', ['$location', '$document', 'asset', function($location, $document, asset) {
            return {
                templateUrl: 'scripts/verifiedpixel-imagelist/views/item-searchbar.html',
                link: function(scope, elem) {
                    var ENTER = 13;

                    scope.focused = false;
                    var input = elem.find('#search-input');

                    scope.searchOnEnter = function($event) {
                        if ($event.keyCode === ENTER) {
                            scope.search();
                            $event.stopPropagation();
                        }
                    };

                    scope.search = function() {
                        $location.search('q', input[0].value || null);
                    };

                    scope.cancel = function() {
                        scope.query = null;
                        input.focus();
                        //to be implemented
                    };

                    //initial query
                    var srch = $location.search();
                    if (srch.q && srch.q !== '') {
                        scope.query = srch.q;
                    } else {
                        scope.query = null;
                    }

                    function closeOnClick() {
                        scope.$apply(function() {
                            scope.focused = false;
                        });
                    }

                    $document.bind('click', closeOnClick);

                    scope.$on('$destroy', function() {
                        $document.unbind('click', closeOnClick);
                    });

                }
            };
        }])

        .directive('vpItemSearch', ['$location', '$timeout', 'asset', 'api', 'tags', 'search', 'metadata',
            function($location, $timeout, asset, api, tags, search, metadata) {
            return {
                scope: {
                    repo: '=',
                    context: '='
                },
                templateUrl: 'scripts/verifiedpixel-imagelist/views/item-search.html',
                link: function(scope, elem) {

                    var input = elem.find('#search-input');

                    function init() {
                        var params = $location.search();
                        scope.query = params.q;
                        scope.flags = false;
                        scope.meta = {};

                        fetchProviders();

                        if (params.repo) {
                            var param_list = params.repo.split(',');
                            scope.repo.archive = param_list.indexOf('archive') >= 0;
                            scope.repo.ingest = param_list.indexOf('ingest') >= 0;
                            scope.repo.published = param_list.indexOf('published') >= 0;
                            scope.repo.text_archive = param_list.indexOf('text_archive') >= 0;
                        }

                        if (!scope.repo) {
                            scope.repo = {'search': 'local'};
                        } else {
                            if (!scope.repo.archive && !scope.repo.ingest && !scope.repo.published && !scope.repo.text_archive) {
                                scope.repo.search = params.repo;
                            } else {
                                scope.repo.search = 'local';
                            }
                        }
                    }

                    init();

                    function fetchProviders() {
                        return api.ingestProviders.query({max_results: 200})
                            .then(function(result) {
                                scope.providers = result._items;
                            });
                    }

                    scope.$on('$locationChangeSuccess', function() {
                        if (scope.query !== $location.search().q) {
                            init();
                        }
                    });

                    function getActiveRepos() {
                        var repos = [];

                        if (scope.repo.search === 'local') {
                            angular.forEach(scope.repo, function(val, key) {
                                if (val && val !== 'local') {
                                    repos.push(key);
                                }
                            });

                            return repos.length ? repos.join(',') : null;

                        } else {
                            return scope.repo.search;
                        }
                    }

                    function getFirstKey(data) {
                        for (var prop in data) {
                            if (data.hasOwnProperty(prop)) {
                                return prop;
                            }
                        }
                    }

                    function getQuery() {
                        var metas = [];
                        angular.forEach(scope.meta, function(val, key) {
                            if (key === '_all') {
                                metas.push(val.join(' '));
                            } else {
                                if (val) {
                                    if (typeof(val) === 'string'){
                                        if (val) {
                                            metas.push(key + ':(' + val + ')');
                                        }
                                    } else {
                                        var subkey = getFirstKey(val);
                                        if (val[subkey]) {
                                            metas.push(key + '.' + subkey + ':(' + val[subkey] + ')');
                                        }
                                    }
                                }
                            }
                        });

                        if (metas.length) {
                            if (scope.query) {
                                return scope.query + ' ' + metas.join(' ');
                            } else {
                                return metas.join(' ');
                            }
                        } else {
                            return scope.query || null;
                        }

                    }

                    scope.focusOnSearch = function() {
                        if (scope.advancedOpen) {
                            scope.toggle();
                        }
                        input.focus();
                    };

                    function updateParam() {
                        scope.query = $location.search().q;
                        $location.search('q', getQuery() || null);
                        $location.search('repo', getActiveRepos());
                        scope.meta = {};
                    }

                    scope.search = function() {
                        updateParam();
                    };

                    scope.$on('key:s', function openSearch() {
                        scope.$apply(function() {
                            scope.flags = {extended: true};
                            $timeout(function() { // call focus when input will be visible
                                input.focus();
                            }, 0, false);
                        });
                    });

                    /*
                     * Converting to object and adding pre-selected subject codes to list in left sidebar
                     */
                    metadata
                        .fetchSubjectcodes()
                        .then(function () {
                            scope.subjectcodes = metadata.values.subjectcodes;
                            return tags.initSelectedFacets();
                        })
                        .then(function (currentTags) {
                            scope.subjectitems = {
                                subject: search.getSubjectCodes(currentTags, scope.subjectcodes)
                            };
                        });

                    /*
                     * Filter content by subject search
                     */
                    scope.subjectSearch = function (item) {
                        tags.initSelectedFacets().then(function (currentTags) {
                            var subjectCodes = search.getSubjectCodes(currentTags, scope.subjectcodes);
                            if (item.subject.length > subjectCodes.length) {
                                /* Adding subject codes to filter */
                                var addItemSubjectName = 'subject.name:(' + item.subject[item.subject.length - 1].name + ')',
                                    query = getQuery(),
                                    q = (query === null ? addItemSubjectName : query + ' ' + addItemSubjectName);

                                $location.search('q', q);
                            } else {
                                /* Removing subject codes from filter */
                                var params = $location.search();
                                if (params.q) {
                                    for (var j = 0; j < subjectCodes.length; j++) {
                                        if (item.subject.indexOf(subjectCodes[j]) === -1) {
                                            var removeItemSubjectName = 'subject.name:(' + subjectCodes[j].name + ')';
                                            params.q = params.q.replace(removeItemSubjectName, '').trim();
                                            $location.search('q', params.q || null);
                                        }
                                    }
                                }
                            }
                        });
                    };
                }
            };
        }])

        /**
         * Item sort component
         */
        .directive('vpItemSortbar', ['search', 'asset', function sortBarDirective(search, asset) {
            return {
                scope: {},
                templateUrl: 'scripts/verifiedpixel-imagelist/views/item-sortbar.html',
                link: function(scope) {
                    scope.sortOptions = search.sortOptions;

                    function getActive() {
                        scope.active = search.getSort();
                    }

                    scope.sort = function sort(field) {
                        search.setSort(field);
                    };

                    scope.toggleDir = function toggleDir($event) {
                        search.toggleSortDir();
                    };

                    scope.$on('$routeUpdate', getActive);
                    getActive();
                }
            };
        }])

        .directive('vpSavedSearchSelect', ['api', 'session', function SavedSearchSelectDirective(api, session) {
            return {
                link: function(scope) {
                    api.query('saved_searches', {}, session.identity).then(function(res) {
                        scope.searches = res._items;
                    });
                }
            };
        }])

        .directive('vpSavedSearches', ['api', 'session', '$location', 'notify', 'gettext', 'asset',
        function(api, session, $location, notify, gettext, asset) {
            return {
                templateUrl: 'scripts/verifiedpixel-imagelist/views/saved-searches.html',
                scope: {},
                link: function(scope) {

                    var resource = api('saved_searches', session.identity);
                    scope.selected = null;
                    scope.editSearch = null;

                    resource.query().then(function(views) {
                        scope.views = views._items;
                    });

                    scope.select = function(view) {
                        scope.selected = view;
                        $location.search(view.filter.query);
                    };

                    scope.edit = function() {
                        scope.editSearch = {};
                    };

                    scope.cancel = function() {
                        scope.editSearch = null;
                    };

                    scope.save = function(editSearch) {

                        editSearch.filter = {query: $location.search()};

                        resource.save({}, editSearch)
                        .then(function(result) {
                            notify.success(gettext('Saved search created'));
                            scope.cancel();
                            scope.views.push(result);
                        }, function() {
                            notify.error(gettext('Error. Saved search not created.'));
                        });
                    };

                    scope.remove = function(view) {
                        resource.remove(view).then(function() {
                            notify.success(gettext('Saved search removed'));
                            _.remove(scope.views, {_id: view._id});
                        }, function() {
                            notify.error(gettext('Error. Saved search not deleted.'));
                        });
                    };
                }
            };
        }])

        .directive('vpSearchContainer', function() {
            return {
                controller: ['$scope', function SearchContainerController($scope) {
                    this.flags = $scope.flags || {};
                }]
            };
        })

        .directive('vpMultiActionBar', ['asset', 'multi',
        function(asset, multi) {
            return {
                controller: 'MultiActionBar',
                controllerAs: 'action',
                templateUrl: 'scripts/verifiedpixel-imagelist/views/multi-action-bar.html',
                link: function(scope) {
                    scope.multi = multi;
                }
            };
        }])

        .directive('vpMediaAll', ['userList', function(userList) {
            return {
                scope: {
                    item: '='
                },
                templateUrl: 'scripts/verifiedpixel-imagelist/views/all-view.html',
                link: function(scope, elem) {

                    scope.$watch('item', reloadData);

                    function reloadData() {
                        scope.originalCreator = null;
                        scope.versionCreator = null;

                        if (scope.item.original_creator) {
                            userList.getUser(scope.item.original_creator)
                            .then(function(user) {
                                scope.originalCreator = user.display_name;
                            });
                        }
                        if (scope.item.version_creator) {
                            userList.getUser(scope.item.version_creator)
                            .then(function(user) {
                                scope.versionCreator = user.display_name;
                            });
                        }
                    }

                    function GPSToFloat(input, ref){
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
                    // check to see if the file latitude record exists before trying to return anything // longitude is there for the sake of completeness
                    if (scope.item.filemeta.GPSInfo.GPSLatitude && scope.item.filemeta.GPSInfo.GPSLongitude) {
                        // lat is always first
                        scope.item.gpslat = GPSToFloat(
                            scope.item.filemeta.GPSInfo.GPSLatitude,
                            scope.item.filemeta.GPSInfo.GPSLatitudeRef 
                        );
                        scope.item.gpslon = GPSToFloat(
                            scope.item.filemeta.GPSInfo.GPSLongitude,
                            scope.item.filemeta.GPSInfo.GPSLongitudeRef
                        );
                    }
                }
            };
        }])

        .directive('vpMediaExif', ['userList', function(userList) {
            return {
                scope: {
                    item: '='
                },
                templateUrl: 'scripts/verifiedpixel-imagelist/views/exif-view.html',
                link: function(scope, elem) {

                    scope.$watch('item', reloadData);

                    function reloadData() {
                        scope.originalCreator = null;
                        scope.versionCreator = null;

                        if (scope.item.original_creator) {
                            userList.getUser(scope.item.original_creator)
                            .then(function(user) {
                                scope.originalCreator = user.display_name;
                            });
                        }
                        if (scope.item.version_creator) {
                            userList.getUser(scope.item.version_creator)
                            .then(function(user) {
                                scope.versionCreator = user.display_name;
                            });
                        }
                    }
                }
            };
        }])


        .directive('vpMediaIzitru', ['userList', function(userList) {
            return {
                scope: {
                    item: '='
                },
                templateUrl: 'scripts/verifiedpixel-imagelist/views/izitru-view.html',
                link: function(scope, elem) {

                    scope.$watch('item', reloadData);

                    function reloadData() {
                        scope.originalCreator = null;
                        scope.versionCreator = null;

                        if (scope.item.original_creator) {
                            userList.getUser(scope.item.original_creator)
                            .then(function(user) {
                                scope.originalCreator = user.display_name;
                            });
                        }
                        if (scope.item.version_creator) {
                            userList.getUser(scope.item.version_creator)
                            .then(function(user) {
                                scope.versionCreator = user.display_name;
                            });
                        }
                    }
                }
            };
        }])

        .directive('vpMediaTineye', ['userList', function(userList) {
            return {
                scope: {
                    item: '='
                },
                templateUrl: 'scripts/verifiedpixel-imagelist/views/tineye-view.html',
                link: function(scope, elem) {

                    scope.$watch('item', reloadData);

                    function reloadData() {
                        scope.originalCreator = null;
                        scope.versionCreator = null;

                        if (scope.item.original_creator) {
                            userList.getUser(scope.item.original_creator)
                            .then(function(user) {
                                scope.originalCreator = user.display_name;
                            });
                        }
                        if (scope.item.version_creator) {
                            userList.getUser(scope.item.version_creator)
                            .then(function(user) {
                                scope.versionCreator = user.display_name;
                            });
                        }
                    }
                }
            };
        }])

        .directive('vpMediaGris', ['userList', function(userList) {
            return {
                scope: {
                    item: '='
                },
                templateUrl: 'scripts/verifiedpixel-imagelist/views/gris-view.html',
                link: function(scope, elem) {

                    scope.$watch('item', reloadData);

                    function reloadData() {
                        scope.originalCreator = null;
                        scope.versionCreator = null;

                        if (scope.item.original_creator) {
                            userList.getUser(scope.item.original_creator)
                            .then(function(user) {
                                scope.originalCreator = user.display_name;
                            });
                        }
                        if (scope.item.version_creator) {
                            userList.getUser(scope.item.version_creator)
                            .then(function(user) {
                                scope.versionCreator = user.display_name;
                            });
                        }
                    }
                }
            };
        }])

        .directive('vpMediaBox', ['$location', 'lock', 'multi', function($location, lock, multi) {
            return {
                restrict: 'A',
                templateUrl: 'scripts/verifiedpixel-imagelist/views/media-box.html',
                link: function(scope, element, attrs) {
                    scope.lock = {isLocked: false};

                    scope.$watch('view', function(view) {
                        switch (view) {
                        case 'mlist':
                        case 'compact':
                            scope.itemTemplate = 'scripts/verifiedpixel-imagelist/views/media-box-list.html';
                            break;
                        default:
                            scope.itemTemplate = 'scripts/verifiedpixel-imagelist/views/media-box-grid.html';
                        }
                    });

                    scope.$watch('item', function(item) {
                        scope.lock.isLocked = item && (lock.isLocked(item) || lock.isLockedByMe(item));
                    });

                    scope.$on('item:lock', function(_e, data) {
                        if (scope.item && scope.item._id === data.item) {
                            scope.lock.isLocked = true;
                            scope.item.lock_user = data.user;
                            scope.item.lock_session = data.lock_session;
                            scope.item.lock_time = data.lock_time;
                            scope.$digest();
                        }
                    });

                    scope.$on('item:unlock', function(_e, data) {
                        if (scope.item && scope.item._id === data.item) {
                            scope.lock.isLocked = false;
                            scope.item.lock_user = null;
                            scope.item.lock_session = null;
                            scope.item.lock_time = null;
                            scope.$digest();
                        }
                    });

                    scope.$on('task:progress', function(_e, data) {
                        if (data.task === scope.item.task_id) {
                            if (data.progress.total === 0) {
                                scope._progress = 10;
                            } else {
                                scope._progress = Math.min(100, Math.round(100.0 * data.progress.current / data.progress.total));
                            }
                            scope.$digest();
                        }
                    });

                    scope.clickAction =  function clickAction(item) {
                        if (typeof scope.preview === 'function') {
                            $location.search('fetch', null);
                            return scope.preview(item);
                        }
                        return false;
                    };

                    scope.toggleSelected = function(item) {
                        multi.toggle(item);
                    };
                }
            };
        }])

        .config(['superdeskProvider', 'assetProvider', function(superdesk, asset) {
            superdesk.activity('/verifiedpixel', {
                description: gettext('Find live and archived content'),
                beta: 1,
                priority: 200,
                category: superdesk.MENU_MAIN,
                label: gettext('Verified Pixel'),
                controller: ImageListController,
                templateUrl: 'scripts/verifiedpixel-imagelist/views/search.html'
            });
        }]);



    MultiActionBarController.$inject = ['multi', 'multiEdit', 'send', 'packages', 'superdesk', 'notify', 'spike', 'authoring'];
    function MultiActionBarController(multi, multiEdit, send, packages, superdesk, notify, spike, authoring) {
        this.send  = function() {
            return send.all(multi.getItems());
        };

        this.sendAs = function() {
            return send.allAs(multi.getItems());
        };

        this.multiedit = function() {
            multiEdit.create(multi.getIds());
            multiEdit.open();
        };

        this.createPackage = function() {
            packages.createPackageFromItems(multi.getItems())
            .then(function(new_package) {
                superdesk.intent('author', 'package', new_package);
            }, function(response) {
                if (response.status === 403 && response.data && response.data._message) {
                    notify.error(gettext(response.data._message), 3000);
                }
            });
        };

        this.spikeItems = function() {
            spike.spikeMultiple(multi.getItems());
            multi.reset();
        };

        this.unspikeItems = function() {
            spike.unspikeMultiple(multi.getItems());
            multi.reset();
        };

        this.canSpikeItems = function() {
            var canSpike = true;
            multi.getItems().forEach(function(item) {
                canSpike = canSpike && authoring.itemActions(item).spike;
            });
            return canSpike;
        };
    }

})();
