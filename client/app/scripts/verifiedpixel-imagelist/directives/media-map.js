'use strict';

angular.module('verifiedpixel.imagelist').directive('vpMediaMap', [
    'userList',
    function(userList) {
      return {
        scope : {item : '='},
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/map-view.html',
      };
    }
]);
