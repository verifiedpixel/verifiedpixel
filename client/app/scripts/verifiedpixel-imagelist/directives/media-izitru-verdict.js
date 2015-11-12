'use strict';

angular.module('verifiedpixel.imagelist').directive('vpMediaIzitruVerdict', [
    function() {
      return {
        scope : {item : '='},
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/izitru-verdict-view.html',
      };
    }
]);
