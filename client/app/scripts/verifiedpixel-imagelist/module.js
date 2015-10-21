define(
  [
    'verifiedpixel-imagelist/services/imagelist',
    'verifiedpixel-imagelist/services/imagetools',
    'verifiedpixel-imagelist/services/tagging',
    'verifiedpixel-imagelist/services/tags',

    'verifiedpixel-imagelist/controllers/multi-action-bar',

    'verifiedpixel-imagelist/directives/search-results',
    'verifiedpixel-imagelist/directives/search-facets',
    'verifiedpixel-imagelist/directives/media-box',
    'verifiedpixel-imagelist/directives/item-rendition',
    'verifiedpixel-imagelist/directives/item-search',
  ],
  function(
      ImageListService,
      ImageToolsService,
      TaggingService,
      TagService,

      MultiActionBarController,

      SearchResultsDirective,
      SearchFacetsDirective,
      MediaBoxDirective,
      ItemRenditionDirective,
      ItemSearchDirective
  ) {
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

  var ImageListController = [
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
  ];

  var objSlice = function (obj, start, end) {
      var sliced = {};
      var i = 0;
      for (var k in obj) {
          if (i >= start && i < end) {
	    sliced[k] = obj[k];
	  }
          i++;
      }

      return sliced;
  };

  angular.module('verifiedpixel.imagelist',
                 [
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
      .service('imagelist', ImageListService)
      .service('imagetools', ImageToolsService)
      .service('tagging', TaggingService)
      .service('tags', TagService)
      .service('verification', [
        'api',
        function(api) {
            this.refreshVerificationResults = function(item, provider) {
                api('manual_verification').save({
                    'item_id': item._id, 'provider': provider
                });
            }
        }
      ])
      .filter('FacetLabels',
              function() {
                return function(input) {
                  if (input.toUpperCase() === 'URGENCY') {
                    return 'News Value';
                  } else {
                    return input;
                  }

                };
              })
      .filter('emailFilter',
              function() {
                return function(str) {
                  return str ? str.replace(/^.*<(.*)>$/g, '\$1') : '';
                };
              })
      .filter('paginate', function() {
        return function(arr, pageNumber, pageSize) {
          pageNumber = pageNumber || 1;
          var end = pageNumber*pageSize,
              start = end-pageSize;
          if (arr.isArray) {
              return (arr || []).slice(start, end);
          } else {
              return objSlice(arr, start, end);
          }
        };
      })
      .controller('MultiActionBar', MultiActionBarController)
      .directive('vpSearchResults', SearchResultsDirective)
      .directive('vpSearchFacets', SearchFacetsDirective)
      .directive('vpMediaBox', MediaBoxDirective)
      .directive('vpItemRendition', ItemRenditionDirective)
      .directive('vpItemSearch', ItemSearchDirective)
      .directive('vpExifOrient',
                 [
                   'imagetools',
                   function(imagetools) {
                     return {
                       restrict : 'A',
                       scope : {
                         orientation : '=',
                       },
                       link : function linkLogic(scope, elem) {
                         scope.$watch('orientation', function(orientation) {
                           imagetools.reOrient(
                               parseInt(scope.orientation || 1, 10), elem);
                         });
                       }
                     };
                   }
                 ])

      .directive(
          'vpItemPreview',
          [
            'asset',
            'commentsService',
            function(asset, commentsService) {
              return {
                templateUrl :
                    'scripts/verifiedpixel-imagelist/views/item-preview.html',
                scope : {
                  item : '=',
                  close : '&',
                  openLightbox : '=',
                  openSingleItem : '='
                },
                link : function(scope) {
                  scope.tab = {selected : 'all'};
                  scope.openTab = function(tab) { scope.tab.selected = tab; };
                  scope.$watch('item', function(item) {
                    scope.selected = {preview : item || null};
                    // get comments count
                    if (item) {
                      commentsService.fetch(item._id).then(function() {
                        scope.item.comments = commentsService.comments;
                      });
                    }
                  });
                }
              };
            }
          ])

      .directive(
          'vpUserMentio',
          [
            'userList',
            function(userList) {
              return {
                templateUrl :
                    'scripts/verifiedpixel-imagelist/views/mentions.html',
                link : function(scope, elem) {
                  scope.users = [];

                  // filter user by given prefix
                  scope.searchUsers = function(prefix) {
                    return userList.get(prefix, 1, 10)
                        .then(function(result) {
                          scope.users = _.sortBy(result._items, 'username');
                        });

                  };

                  scope.selectUser = function(user) {
                    return '@' + user.username;
                  };

                  scope.$watchCollection(
                      function() { return $('.users-list-embed>li.active'); },
                      function(newValue) {
                        if (newValue.hasClass('active')) {
                          $('.mentio-menu').scrollTop(newValue.position().top);
                        }
                      });
                }
              };
            }
          ])

      /**
       * Item sort component
       */
      .directive('vpSearchContainer',
                 function() {
                   return {
                     controller : [
                       '$scope',
                       function SearchContainerController($scope) {
                         this.flags = $scope.flags || {};
                       }
                     ]
                   };
                 })

      .directive(
          'vpMultiActionBar',
          [
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
          ])

      .directive(
          'vpMediaAll',
          [
            function() {
              return {
                templateUrl :
                    'scripts/verifiedpixel-imagelist/views/all-view.html',
                scope : {item : '=', openTab : '&'},
              };
            }
          ])
      .directive(
          'vpExifWhere',
          [
            function() {
              return {
                templateUrl :
                    'scripts/verifiedpixel-imagelist/views/exif-where-view.html',
                scope : {item : '='},
              };
            }
          ])
      .directive(
          'vpExifCamera',
          [
            function() {
              return {
                templateUrl :
                    'scripts/verifiedpixel-imagelist/views/exif-camera-view.html',
                scope : {item : '='},
              };
            }
          ])

      .directive(
          'vpMediaMap',
          [
            'userList',
            function(userList) {
              return {
                scope : {item : '='},
                templateUrl :
                    'scripts/verifiedpixel-imagelist/views/map-view.html',
              };
            }
          ])

      .directive(
          'vpMediaExif',
          [
            'userList',
            function(userList) {
              return {
                scope : {item : '='},
                templateUrl :
                    'scripts/verifiedpixel-imagelist/views/exif-view.html',
              };
            }
          ])

      .directive(
          'vpMediaIzitru',
          [
            function() {
              return {
                scope : {item : '='},
                templateUrl :
                    'scripts/verifiedpixel-imagelist/views/izitru-view.html',
              };
            }
          ])
      .directive(
          'vpMediaIzitruVerdict',
          [
            function() {
              return {
                scope : {item : '='},
                templateUrl :
                    'scripts/verifiedpixel-imagelist/views/izitru-verdict-view.html',
              };
            }
          ])
      .directive(
          'vpMediaIzitruDevice',
          [
            function() {
              return {
                scope : {item : '='},
                templateUrl :
                    'scripts/verifiedpixel-imagelist/views/izitru-device-view.html',
              };
            }
          ])
      .directive(
          'vpMediaIzitruDeviceInsight',
          [
            function() {
              return {
                scope : {item : '='},
                templateUrl :
                    'scripts/verifiedpixel-imagelist/views/izitru-device-insight-view.html',
              };
            }
          ])

      .directive(
          'vpMediaTineye',
          [
            'userList',
            'verification',
            function(userList, verification) {
              return {
                scope : {item : '='},
                templateUrl :
                    'scripts/verifiedpixel-imagelist/views/tineye-view.html',
                link : function(scope, elem) {
                  scope.refreshVerificationResults = verification.refreshVerificationResults;
                }
              };
            }
          ])

      .directive(
          'vpMediaGris',
          [
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
          ])

      .directive(
          'vpMediaComments',
          [
            'userList',
            'tagging',
            function(userList, tagging) {
              return {
                scope : {item : '='},
                templateUrl :
                    'scripts/verifiedpixel-imagelist/views/comments-view.html',
                link : function(scope) {
                  tagging.getTags(scope);
                  scope.addTag = tagging.addTag;
                  scope.removeTag = tagging.removeTag;
                }
              };
            }
          ])

      .directive(
          'vpCommentText',
          [
            '$compile',
            function($compile) {
              return {
                scope : {comment : '='},
                link : function(scope, element, attrs) {

                  var html;

                  // replace new lines with paragraphs
                  html = attrs.text.replace(/(?:\r\n|\r|\n)/g, '</p><p>');

                  // map user mentions
                  var mentioned = html.match(/\@([a-zA-Z0-9-_.]\w+)/g);
                  _.each(mentioned, function(token) {
                    var username = token.substring(1, token.length);
                    if (scope.comment.mentioned_users &&
                        scope.comment.mentioned_users[username]) {
                      html = html.replace(
                          token, '<i sd-user-info data-user="' +
                                     scope.comment.mentioned_users[username] +
                                     '">' + token + '</i>');
                    }
                  });

                  // build element
                  element.html('<p><b>' + attrs.name + '</b> : ' + html +
                               '</p>');

                  $compile(element.contents())(scope);
                }
              };
            }
          ])

      .directive('vpGlossary',
                 [
                   'userList',
                   function(userList) {
                     return {
                       templateUrl :
                           'scripts/verifiedpixel-imagelist/views/glossary.html'
                     };
                   }
                 ])

      .config([
        'superdeskProvider',
        'assetProvider',
        function(superdesk, asset) {
          superdesk.activity('/verifiedpixel', {
            description : gettext('Find live and archived content'),
            beta : 1,
            priority : 200,
            category : superdesk.MENU_MAIN,
            label : gettext('Verified Pixel'),
            controller : ImageListController,
            templateUrl : 'scripts/verifiedpixel-imagelist/views/search.html'
          });
        }
      ]);

});
