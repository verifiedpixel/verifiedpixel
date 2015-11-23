'use strict';

angular.module('verifiedpixel.imagelist').directive('vpMediaIzitru', [
    function() {
      return {
        scope : {item : '='},
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/izitru-view.html',
      };
    }
]);
