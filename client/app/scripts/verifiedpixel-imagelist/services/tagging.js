(function() {
    'use strict';

    TaggingService.$inject = ['metadata', 'api'];
    function TaggingService(metadata, api) {

        var vppTags;
        this.getTags = function(scope) {
            if (typeof vppTags === 'undefined') {
                metadata.initialize().then(function() {
                    scope.metadata = metadata.values;
                    vppTags = {};
                    metadata.values.vpp_tags.forEach(function(elem) {
                        vppTags[elem.qcode] = elem.name;
                    });
                    scope.vppTags = vppTags;
                });
            } else {
                scope.vppTags = vppTags;
            }
        };
        this.addTag = function(item, tagCode) {
            var item_clone = _.clone(item);
            var tags = item.vpp_tag || [];
            tags.push(tagCode);
            item_clone._links.self.href = item_clone._links.self.href.replace('search/', 'archive/');
            item_clone._links.self.title = 'Archive';
            api('archive').save(item_clone, {'vpp_tag': tags});
        };
        this.removeTag = function(item, tagCode) {
            var item_clone = _.clone(item);
            var tags = item.vpp_tag;
            tags.splice(tags.indexOf(tagCode), 1);
            item_clone._links.self.href = item_clone._links.self.href.replace('search/', 'archive/');
            item_clone._links.self.title = 'Archive';
            api('archive').save(item_clone, {'vpp_tag': tags});
        };

    }


    angular.module('verifiedpixel.imagelist')
        .service('tagging', TaggingService);
})();
