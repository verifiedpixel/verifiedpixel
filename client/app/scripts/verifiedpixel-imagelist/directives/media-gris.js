'use strict';

angular.module('verifiedpixel.imagelist').directive('vpMediaGris', [
    'userList',
    'verification',
    function(userList, verification) {
      return {
        scope : {item : '='},
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/gris-view.html',
        link : function(scope, elem) {
          scope.refreshVerificationResults = verification.refreshVerificationResults;
        },
      };
    }
]);
