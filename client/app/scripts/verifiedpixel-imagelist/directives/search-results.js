(function() {
    'use strict';

    /**
     * Item list with sidebar preview
     */
    angular.module('verifiedpixel.imagelist')
    .directive('vpSearchResults', ['$timeout', '$location', 'api', 'preferencesService', 'packages', 'tags', 'asset', 'imagelist',
        function($timeout, $location, api, preferencesService, packages, tags, asset, imagelist) {
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
            scope: {
                items: '=',
                desk: '=',
                repo: '=',
                context: '='
            },
            link: function(scope, elem, attr, controller) {

                var GRID_VIEW = 'mgrid',
                    LIST_VIEW = 'compact';

                var multiSelectable = (attr.multiSelectable === undefined) ? false : true;

                scope.flags = controller.flags;
                scope.selected = scope.selected || {};

                // let's get access to the DOM
                scope.$watch('items', function(){
                    $timeout(function(){
                        filmstrip();
                    });
                });
                var filmstrip = function(){
                    // are there any slides?
                    var slideLen = $('.slides li').length;
                    if (slideLen > 0) {
                        var container = $('.shadow-list-holder');
                        var containerW = container.width();
                        var activeSlide = $('.slides .active');
                        var activeSlideW = activeSlide.width();
                        var activeSlideOffset = activeSlide.position().left;
                            container.scrollLeft((activeSlideOffset - ((containerW / 2) - (activeSlideW / 2))) - 2);
                    }
                };
                scope.preview = function preview(item) {
                    if (multiSelectable) {
                        if (_.findIndex(scope.selectedList, {_id: item._id}) === -1) {
                            scope.selectedList.push(item);
                        } else {
                            _.remove(scope.selectedList, {_id: item._id});
                        }
                    }
                    var results = (item && item.verification) ? item.verification.results : null;
                    var updatePreview = function() {
                        scope.selected.preview = item;
                        if (scope.selected.preview !== undefined) {
                            $timeout(function(){
                                filmstrip();
                            });
                        }
                        $location.search('_id', item ? item._id : null);
                    };
                    imagelist.markViewed(item);
                    if (typeof results === 'string') {
                        api('verification_results')
                        .getById(results)
                        .then(function(new_results) {
                            item.verification.results = new_results;
                            updatePreview();
                        });
                    } else {
                        updatePreview();
                    }
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
    }]);

})();
