'use strict';

angular.module('verifiedpixel.imagelist').directive('vpItemPreview', [
    'asset',
    'commentsService',
    function(asset, commentsService) {
      return {
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/item-preview.html',
        scope : {
          item : '=',
          close : '&',
          openLightbox : '=',
          openSingleItem : '='
        },
        link : function(scope) {
          scope.tab = {selected : 'all'};
          scope.openTab = function(tab) { scope.tab.selected = tab; };
          scope.$watch('item', function(item) {
            scope.selected = {preview : item || null};
            // get comments count
            if (item) {
              commentsService.fetch(item._id).then(function() {
                scope.item.comments = commentsService.comments;
              });
            }
          });
        }
      };
    }
]);
