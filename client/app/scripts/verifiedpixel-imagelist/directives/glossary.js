'use strict';

angular.module('verifiedpixel.imagelist').directive('vpGlossary', [
   'userList',
   function(userList) {
     return {
       templateUrl :
           'scripts/verifiedpixel-imagelist/views/glossary.html'
     };
   }
]);
