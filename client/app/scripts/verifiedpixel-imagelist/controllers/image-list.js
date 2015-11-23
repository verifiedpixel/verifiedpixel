'use strict';

function keysToLowerCase(obj) {
    var output = {};
    for (var i in obj) {
      if (Object.prototype.toString.apply(obj[i]) === '[object Object]') {
        output[i.toLowerCase()] = keysToLowerCase(obj[i]);
      } else {
        output[i.toLowerCase()] = obj[i];
      }
    }
    return output;
}

angular.module('verifiedpixel.imagelist').controller('ImageListController', [
    '$scope',
    '$location',
    'api',
    'imagelist',
    'notify',
    'session',
    'imagetools',
    function($scope, $location, api, imagelist, notify, session, imagetools) {
      $scope.context = 'search';

      $scope.$on('item:deleted:archive:text', itemDelete);
      $scope.$on('item:created', refresh);
      $scope.$on('item:fetch', refresh);
      $scope.$on('item:spike', refresh);
      $scope.$on('item:updated', refresh);

      function itemDelete(e, data) {
        if (session.identity._id === data.user) {
          refresh();
        }
      }

      $scope.repo = {
        ingest : true,
        archive : true,
        text_archive : true,
        published : true
      };

      var refreshInProgress = false;
      var needMoreRefresh = false;

      function refresh() {
        $scope.$broadcast('vpp::multi.reset');
        if (refreshInProgress) {
            needMoreRefresh = true;
            return;
        }
        refreshInProgress = true;
        var query = _.omit($location.search(), '_id');
        if (!_.isEqual(_.omit(query, 'page'), _.omit(oldQuery, 'page'))) {
          $location.search('page', null);
        }

        var criteria = imagelist.query($location.search()).getCriteria(true);
        var provider = 'search';
        if (criteria.repo) {
          provider = criteria.repo;
        }

        if ($scope.repo.search) {
          if ($scope.repo.search !== 'local') {
            provider = $scope.repo.search;
          } else if (criteria.repo.indexOf(',') >= 0) {
            provider = 'search';
          }
        }

        api.query(provider, criteria)
            .then(function(results) {
              // normalize exif filemata fields because
              // sometimes we get lowercase field names, and somtimes camel case
              // this function just makes them all lower case
              // also makes sure that a filemeta object always exists
              var processedItems = [];
              angular.forEach(results._items, function(item) {
                var filemeta = (item.filemeta) ? item.filemeta : {};
                var filemetaLowered = keysToLowerCase(filemeta);
                // convert enum and rational values to readable values
                item.converted_exif =
                    imagetools.convertExif(filemetaLowered, filemetaLowered);
                processedItems.push(item);
              });
              results._items = processedItems;
              $scope.items = results;
              refreshInProgress = false;
              if (needMoreRefresh) {
                needMoreRefresh = false;
                refresh();
              }
            });

        oldQuery = query;
      }

      var oldQuery = _.omit($location.search(), '_id');
      $scope.$watch(function getSearchParams() {
        return _.omit($location.search(), '_id');
      }, refresh, true);
    }

]);
