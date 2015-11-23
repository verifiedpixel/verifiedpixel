'use strict';

angular.module('verifiedpixel.imagelist').directive('vpSearchFacets', [
    /**
     * Item filters sidebar
     */
    '$location', 'desks', 'privileges', 'tags', 'tagging',
     function($location, desks, privileges, tags, tagging) {
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
                tagging.getTags(scope);
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
                        'state':{},
                        'make':{},
                        'capture_location': {},
                        'izitru': {},
                        'original_source': {},
                        'vpp_tag': {}
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

                            _.forEach(scope.items._aggregations.make.buckets, function(make) {
                                scope.aggregations.make[make.key] = make.doc_count;
                            });

                            _.forEach(scope.items._aggregations.capture_location.buckets, function(capture_location) {
                                scope.aggregations.capture_location[capture_location.key] = capture_location.doc_count;
                            });

                            _.forEach(scope.items._aggregations.izitru.buckets, function(izitru) {
                                scope.aggregations.izitru[izitru.key] = izitru.doc_count;
                            });

                            _.forEach(scope.items._aggregations.vpp_tag.buckets, function(tag) {
                                scope.aggregations.vpp_tag[tag.key] = tag.doc_count;
                            });

                            _.forEach(scope.items._aggregations.original_source.buckets, function(original_source) {
                                scope.aggregations.original_source[original_source.key] = original_source.doc_count;

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
    }

]);
