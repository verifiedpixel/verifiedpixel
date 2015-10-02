define([], function() {
    'use strict';

    return ['$location', 'lock', 'multi', function($location, lock, multi) {
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
    }];

});
