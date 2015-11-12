'use strict';

angular.module('verifiedpixel.imagelist').directive('vpExifOrient', [
    'imagetools',
    function(imagetools) {
      return {
        restrict : 'A',
        scope : {
          orientation : '=',
        },
        link : function linkLogic(scope, elem) {
          scope.$watch('orientation', function(orientation) {
            imagetools.reOrient(
                parseInt(scope.orientation || 1, 10), elem);
          });
        }
      };
    }
])
