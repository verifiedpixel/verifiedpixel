(function() {
    'use strict';

    /**
     * Item filters sidebar
     */
    angular.module('verifiedpixel.imagelist')
    .directive('vpItemRendition', ['imagelist', function (imagelist) {
        return {
            templateUrl: 'scripts/verifiedpixel-imagelist/views/item-rendition.html',
            scope: {
                item: '=',
                rendition: '@',
                ratio: '=?'
            },
            link: function linkLogic(scope, elem) {

                scope.$watch('item.renditions[rendition].href', function(href) {
                    var figure = elem.find('figure'),
                        oldImg = figure.find('img').css('opacity', 0.5);
                    if (href) {
                        var img = new Image();
                        img.onload = function() {
                            if (oldImg.length) {
                                oldImg.replaceWith(img);
                            } else {
                                figure.html(img);
                            }
                            _calcRatio();
                        };

                        img.onerror = function() {
                            figure.html('');
                        };
                        img.src = href;
                        if (scope.item.converted_exif.orientation) {
                            imagelist.reOrient(parseInt(scope.item.converted_exif.orientation || 1, 10), $(img));
                        }
                    }
                });

                var stopRatioWatch = scope.$watch('ratio', function(val) {
                    if (val === undefined) {
                        stopRatioWatch();
                    }
                    calcRatio();
                });

                var calcRatio = _.debounce(_calcRatio, 150);

                function _calcRatio() {
                    var el = elem.find('figure');
                    if (el && scope.ratio) {
                        var img = el.find('img')[0];
                        var ratio = img ? img.naturalWidth / img.naturalHeight : 1;
                        if (scope.ratio > ratio) {
                            el.parent().addClass('portrait');
                        } else {
                            el.parent().removeClass('portrait');
                        }
                    }
                }
            } // end link
        };
    }])

})();
