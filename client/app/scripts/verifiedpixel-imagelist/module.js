(function() {
    'use strict';

    ImageListController.$inject = ['$scope', '$location', 'api', 'gettext', 'upload', 'isArchivedFilterSelected', '$q'];
    function ImageListController($scope, $location, api, gettext, upload, isArchivedFilterSelected, $q) {
        $scope.maxResults = 25;
        $scope.states = [
            {name: 'active', code: 'open', text: gettext('Active images')},
            {name: 'archived', code: 'closed', text: gettext('Archived images')}
        ];
        $scope.activeState = isArchivedFilterSelected ? $scope.states[1] : $scope.states[0];
        $scope.creationStep = 'Details';
        $scope.imageMembers = [];
        $scope.changeState = function(state) {
            $scope.activeState = state;
            $location.path('/verifiedpixel/' + state.name);
            fetchImages();
        };
        $scope.modalActive = false;

        function clearCreateImageForm() {
            $scope.preview = {};
            $scope.progress = {width: 0};
            $scope.newImage = {
                title: '',
                description: ''
            };
            $scope.newImageError = '';
            $scope.creationStep = 'Details';
            $scope.imageMembers = [];
        }
        clearCreateImageForm();

        $scope.cancelCreate = function() {
            clearCreateImageForm();
            $scope.newImageModalActive = false;
        };
        $scope.openNewImage = function() {
            $scope.newImageModalActive = true;
        };

        $scope.createImage = function() {
            var members = _.map($scope.imageMembers, function(obj) {
                return {user: obj._id};
            });
            var promise = angular.equals({}, $scope.preview) ? $q.when() : $scope.upload($scope.preview);
            return promise.then(function() {
                return api.images.save({
                    title: $scope.newImage.title,
                    description: $scope.newImage.description,
                    picture_url: $scope.newImage.picture_url,
                    picture: $scope.newImage.picture,
                    members: members
                }).then(function(image) {
                    $scope.edit(image);
                }, function(error) {
                    //error handler
                    $scope.newImageError = gettext('Something went wrong. Please try again later');
                });
            });
        };

        $scope.upload = function(config) {
            var form = {};
            if (config.img) {
                form.media = config.img;
            } else if (config.url) {
                form.URL = config.url;
            } else {
                return;
            }
            // return a promise of upload which will call the success/error callback
            return api.upload.getUrl().then(function(url) {
                return upload.start({
                    method: 'POST',
                    url: url,
                    data: form
                })
                .then(function(response) {
                    if (response.data._status === 'ERR'){
                        return;
                    }
                    var picture_url = response.data.renditions.viewImage.href;
                    $scope.newImage.picture_url = picture_url;
                    $scope.newImage.picture = response.data._id;
                }, null, function(progress) {
                    $scope.progress.width = Math.round(progress.loaded / progress.total * 100.0);
                });
            });
        };

        $scope.remove = function(image) {
            _.remove($scope.images._items, image);
        };

        $scope.edit = function(image) {
            $location.path('/verifiedpixel/edit/' + image._id);
        };

        $scope.switchTab = function(newTab) {
            $scope.creationStep = newTab;
        };

        $scope.addMember = function(user) {
            $scope.imageMembers.push(user);
        };

        $scope.removeMember = function(user) {
            $scope.imageMembers.splice($scope.imageMembers.indexOf(user), 1);
        };

        function getCriteria() {
            var params = $location.search(),
                criteria = {
                    max_results: $scope.maxResults,
                    embedded: {'original_creator': 1},
                    sort: '[("versioncreated", -1)]',
                    source: {
                        query: {filtered: {filter: {term: {image_status: $scope.activeState.code}}}}
                    }
                };
            if (params.q) {
                criteria.source.query.filtered.query = {
                    query_string: {
                        query: '*' + params.q + '*',
                        fields: ['title', 'description']
                    }
                };
            }
            if (params.page) {
                criteria.page = parseInt(params.page, 10);
            }
            return criteria;
        }

        function fetchImages() {
            api.images.query(getCriteria()).then(function(images) {
                $scope.images = images;
            });
        }

        // initialize images list
        fetchImages();
        // fetch when maxResults is updated from the searchbar-directive
        $scope.$watch('maxResults', fetchImages);
        // fetch when criteria are updated from url (searchbar-directive)
        $scope.$on('$routeUpdate', fetchImages);
    }

    var app = angular.module('verifiedpixel.imagelist', []);
    app.config(['apiProvider', function(apiProvider) {
        apiProvider.api('images', {
            type: 'http',
            backend: {rel: 'images'}
        });
    }]).config(['superdeskProvider', function(superdesk) {
        superdesk
            .activity('/verifiedpixel', {
                label: gettext('Image List'),
                controller: ImageListController,
                templateUrl: 'scripts/verifiedpixel-imagelist/views/list-pane.html',
                category: superdesk.MENU_MAIN,
                resolve: {isArchivedFilterSelected: function() {return false;}}
            }).activity('/verifiedpixel/active', {
                label: gettext('Image List'),
                controller: ImageListController,
                templateUrl: 'scripts/verifiedpixel-imagelist/views/main.html',
                resolve: {isArchivedFilterSelected: function() {return false;}}
            }).activity('/verifiedpixel/archived', {
                label: gettext('Image List'),
                controller: ImageListController,
                templateUrl: 'scripts/verifiedpixel-imagelist/views/main.html',
                resolve: {isArchivedFilterSelected: function() {return true;}}
            });
    }]);
    app.filter('username', ['session', function usernameFilter(session) {
        return function getUsername(user) {
            return user ? user.display_name || user.username : null;
        };
    }]);
    app.directive('sdPlainImage', ['notify', function(notify) {
        return {
            scope: {
                src: '=',
                progressWidth: '='
            },
            link: function(scope, elem) {
                scope.$watch('src', function(src) {
                    elem.empty();
                    if (src) {
                        var img = new Image();
                        img.onload = function() {
                            scope.progressWidth = 80;

                            if (this.width < 320 || this.height < 240) {
                                scope.$apply(function() {
                                    notify.pop();
                                    notify.error(gettext('Sorry, but image image must be at least 320x240 pixels big.'));
                                    scope.src = null;
                                    scope.progressWidth = 0;
                                });

                                return;
                            }
                            elem.append(img);
                            scope.$apply(function() {
                                scope.progressWidth = 0;
                            });
                        };
                        img.src = src;
                    }
                });
            }
        };
    }]).directive('ifBackgroundImage', function() {
        return {
            restrict: 'A',
            scope: {
                ifBackgroundImage: '@'
            },
            link: function(scope, element, attrs) {
                var url = scope.ifBackgroundImage;
                if (url) {
                    element.css({
                        'background-image': 'url(' + url + ')'
                    });
                }
            }
        };
    })
    .directive('lbUserSelectList', ['$filter', 'api', function($filter, api) {
            return {
                scope: {
                    members: '=',
                    onchoose: '&'
                },
                templateUrl: 'scripts/bower_components/superdesk/client/app/scripts/superdesk-desks/views/user-select.html',
                link: function(scope, elem, attrs) {

                    var ARROW_UP = 38, ARROW_DOWN = 40, ENTER = 13;

                    scope.selected = null;
                    scope.search = null;
                    scope.users = {};

                    var _refresh = function() {
                        scope.users = {};
                        return api('users').query({where: JSON.stringify({
                            '$or': [
                                {username: {'$regex': scope.search, '$options': '-i'}},
                                {first_name: {'$regex': scope.search, '$options': '-i'}},
                                {last_name: {'$regex': scope.search, '$options': '-i'}},
                                {email: {'$regex': scope.search, '$options': '-i'}}
                            ]
                        })})
                        .then(function(result) {
                            scope.users = result;
                            scope.users._items = _.filter(scope.users._items, function(item) {
                                var found = false;
                                _.each(scope.members, function(member) {
                                    if (member._id === item._id) {
                                        found = true;
                                    }
                                });
                                return !found;
                            });
                            scope.selected = null;
                        });
                    };
                    var refresh = _.debounce(_refresh, 1000);

                    scope.$watch('search', function() {
                        if (scope.search) {
                            refresh();
                        }
                    });

                    function getSelectedIndex() {
                        if (scope.selected) {
                            var selectedIndex = -1;
                            _.each(scope.users._items, function(item, index) {
                                if (item === scope.selected) {
                                    selectedIndex = index;
                                }
                            });
                            return selectedIndex;
                        } else {
                            return -1;
                        }
                    }

                    function previous() {
                        var selectedIndex = getSelectedIndex(),
                        previousIndex = _.max([0, selectedIndex - 1]);
                        if (selectedIndex > 0) {
                            scope.select(scope.users._items[previousIndex]);
                        }
                    }

                    function next() {
                        var selectedIndex = getSelectedIndex(),
                        nextIndex = _.min([scope.users._items.length - 1, selectedIndex + 1]);
                        scope.select(scope.users._items[nextIndex]);
                    }

                    elem.bind('keydown keypress', function(event) {
                        scope.$apply(function() {
                            switch (event.which) {
                                case ARROW_UP:
                                    event.preventDefault();
                                    previous();
                                    break;
                                case ARROW_DOWN:
                                    event.preventDefault();
                                    next();
                                    break;
                                case ENTER:
                                    event.preventDefault();
                                    if (getSelectedIndex() >= 0) {
                                        scope.choose(scope.selected);
                                    }
                                    break;
                            }
                        });
                    });

                    scope.choose = function(user) {
                        scope.onchoose({user: user});
                        scope.search = null;
                    };

                    scope.select = function(user) {
                        scope.selected = user;
                    };
                }
            };
        }]);
})();
