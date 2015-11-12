'use strict';

angular.module('verifiedpixel.imagelist').directive('vpMultiActionBar', [
    'multi',
    function(multi) {
      return {
        controller : 'MultiActionBar',
        controllerAs : 'action',
        templateUrl :
            'scripts/verifiedpixel-imagelist/views/multi-action-bar.html',
        link : function(scope) { scope.multi = multi; }
      };
    }
]);
