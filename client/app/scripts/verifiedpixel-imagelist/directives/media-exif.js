'use strict';

angular.module('verifiedpixel.imagelist').directive('vpMediaExif', [
    'userList',
    function(userList) {
      return {
        scope : {item : '='},
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/exif-view.html',
      };
    }
]);
