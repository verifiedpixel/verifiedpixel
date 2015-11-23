'use strict';

angular.module('verifiedpixel.imagelist').directive('vpMediaIzitruDeviceInsight', [
    function() {
      return {
        scope : {item : '='},
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/izitru-device-insight-view.html',
      };
    }
]);
