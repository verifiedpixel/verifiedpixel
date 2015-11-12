'use strict';

angular.module('verifiedpixel.imagelist').directive('vpMediaIzitruDevice', [
    function() {
      return {
        scope : {item : '='},
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/izitru-device-view.html',
      };
    }
]);
