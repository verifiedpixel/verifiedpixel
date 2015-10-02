define([], function() {
    'use strict';

        /**
         * Item search component
         */
        return ['$location', '$timeout', 'asset', 'api', 'tags', 'imagelist', 'metadata',
            function($location, $timeout, asset, api, tags, imagelist, metadata) {
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
                                subject: imagelist.getSubjectCodes(currentTags, scope.subjectcodes)
                            };
                        });

                    /*
                     * Filter content by subject search
                     */
                    scope.subjectSearch = function (item) {
                        tags.initSelectedFacets().then(function (currentTags) {
                            var subjectCodes = imagelist.getSubjectCodes(currentTags, scope.subjectcodes);
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
        }];

});
