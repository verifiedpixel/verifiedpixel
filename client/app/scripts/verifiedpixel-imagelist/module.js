(function() {
    'use strict';

     angular.module('verifiedpixel.imagelist', [
       'ngMap',
       'mentio',
       'superdesk.api',
       'superdesk.users',
       'superdesk.desks',
       'superdesk.activity',
       'superdesk.list',
       'superdesk.authoring.metadata',
       'superdesk.keyboard',
       'ui.bootstrap'
     ])

     .config([
        'superdeskProvider',
        'assetProvider',
        function(superdesk, asset) {
          superdesk.activity('/verifiedpixel', {
            label: gettext('Verified Pixel'),
            description: gettext('Find live and archived content'),
            controller: 'ImageListController',
            templateUrl: 'scripts/verifiedpixel-imagelist/views/search.html',
            category: superdesk.MENU_MAIN,
            adminTools: true,
            priority: 200
          });
        }
      ]);

})();
