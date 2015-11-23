'use strict';

angular.module('verifiedpixel.imagelist').directive('vpExifCamera', [
    function() {
      return {
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/exif-camera-view.html',
        scope : {item : '='},
      };
    }
])
