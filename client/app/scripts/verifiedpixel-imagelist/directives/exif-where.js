'use strict';

angular.module('verifiedpixel.imagelist').directive('vpExifWhere', [
    function() {
      return {
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/exif-where-view.html',
        scope : {item : '='},
      };
    }
]);
