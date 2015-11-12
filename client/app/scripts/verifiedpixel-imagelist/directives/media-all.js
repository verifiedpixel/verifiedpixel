'use strict';

angular.module('verifiedpixel.imagelist').directive('vpMediaAll', [
    function() {
      return {
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/all-view.html',
        scope : {item : '=', openTab : '&'},
      };
    }
]);
