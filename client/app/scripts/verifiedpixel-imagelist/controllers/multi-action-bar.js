(function() {
    'use strict';

    MultiActionBarController.$inject = ['multi', 'multiEdit', 'send', 'packages', 'superdesk', 'notify', 'spike', 'authoring', 'api', '$http', '$scope', '$window', 'imagelist', 'tagging'];
    function MultiActionBarController(multi, multiEdit, send, packages, superdesk, notify, spike, authoring, api, $http, $scope, $window, imagelist, tagging) {
        var ctrl = this;

        tagging.getTags($scope);

        this.download_queue = [];

        this.download = function() {
            // implement multi file download
            var added = 0;
            var items = multi.getItems();
            var items_ids = items.map(function(item) { return item._id });
            api.save('verifiedpixel_zip', {"items": items_ids}).then(function(result) {
                ctrl.download_queue.push(result._id);
            });
        };

        this.addTag = function(tagCode) {
            multi.getItems().forEach(function(item) {
                tagging.addTag(item, tagCode);
            });
        };

        $scope.$on('vpp::multi.reset', function(_e) {
            multi.reset();
        });

        $scope.$on('verifiedpixel_zip:ready', function(_e, data) {
            var id = data.id;
            var index_in_queue = ctrl.download_queue.indexOf(id);
            if (index_in_queue >= 0) {
                ctrl.download_queue.splice(index_in_queue, 1);
                $window.open(data.url);
            } else {
                console.log("not in queue:");
                console.log(index_in_queue);
                console.log(id);
                console.log(ctrl.download_queue);
            }
        });

        this.delete = function() {
            // use spike to delete
            spike.spikeMultiple(multi.getItems());
            multi.reset();
        };

        this.send  = function() {
            return send.all(multi.getItems());
        };

        this.sendAs = function() {
            return send.allAs(multi.getItems());
        };

        this.multiedit = function() {
            multiEdit.create(multi.getIds());
            multiEdit.open();
        };

        this.createPackage = function() {
            packages.createPackageFromItems(multi.getItems())
            .then(function(new_package) {
                superdesk.intent('author', 'package', new_package);
            }, function(response) {
                if (response.status === 403 && response.data && response.data._message) {
                    notify.error(gettext(response.data._message), 3000);
                }
            });
        };

        this.spikeItems = function() {
            spike.spikeMultiple(multi.getItems());
            multi.reset();
        };

        this.unspikeItems = function() {
            spike.unspikeMultiple(multi.getItems());
            multi.reset();
        };

        this.canSpikeItems = function() {
            var canSpike = true;
            multi.getItems().forEach(function(item) {
                canSpike = canSpike && authoring.itemActions(item).spike;
            });
            return canSpike;
        };
    }

    angular.module('verifiedpixel.imagelist')
        .controller('MultiActionBar', MultiActionBarController)

})();

