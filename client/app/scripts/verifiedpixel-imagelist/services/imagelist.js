'use strict';

angular.module('verifiedpixel.imagelist').service('imagelist', [
    '$location',
    'gettext',
    'api',
    function ($location, gettext, api) {

      var sortOptions = [
        {field : 'firstcreated', label : gettext('Created')},
        {field : 'versioncreated', label : gettext('Updated')},
        {
          field : 'verification.stats.izitru.verdict',
          label : gettext('Izitru Verdict')
        },
        {
          field : 'verification.stats.izitru.location',
          label : gettext('Izitru Location')
        },
        {
          field : 'verification.stats.incandescent.total_google',
          label : gettext('GRIS Results')
        },
        {
          field : 'verification.stats.tineye.total',
          label : gettext('Tineye Results')
        },
        {field : 'urgency', label : gettext('News Value')},
        {field : 'anpa_category.name', label : gettext('Category')},
        {field : 'slugline', label : gettext('Keyword')},
        {field : 'priority', label : gettext('Priority')}
      ];

      function getSort() {
        var sort = ($location.search().sort || 'firstcreated:desc').split(':');
        return angular.extend(_.find(sortOptions, {field : sort[0]}),
                              {dir : sort[1]});
      }

      function sort(field) {
        var option = _.find(sortOptions, {field : field});
        setSortSearch(option.field, option.defaultDir || 'desc');
      }

      function toggleSortDir() {
        var sort = getSort();
        var dir = sort.dir === 'asc' ? 'desc' : 'asc';
        setSortSearch(sort.field, dir);
      }

      function setSortSearch(field, dir) {
        $location.search('sort', field + ':' + dir);
        $location.search('page', null);
      }

      /*
       * Function for finding object by string array for subject codes
       */
      this.getSubjectCodes = function(currentTags, subjectcodes) {
        var queryArray = currentTags.selectedParameters, filteredArray = [];
        if (!$location.search().q) {
          return filteredArray;
        }
        for (var i = 0, queryArrayLength = queryArray.length;
             i < queryArrayLength; i++) {
          var queryArrayElement = queryArray[i];
          if (queryArrayElement.indexOf('subject.name') !== -1) {
            var elementName = queryArrayElement.substring(
                queryArrayElement.lastIndexOf('(') + 1,
                queryArrayElement.lastIndexOf(')'));
            for (var j = 0, subjectCodesLength = subjectcodes.length;
                 j < subjectCodesLength; j++) {
              if (subjectcodes[j].name === elementName) {
                filteredArray.push(subjectcodes[j]);
              }
            }
          }
        }
        return filteredArray;
      };

      // sort public api
      this.setSort = sort;
      this.getSort = getSort;
      this.sortOptions = sortOptions;
      this.toggleSortDir = toggleSortDir;

      /**
       * Single query instance
       */
      function Query(params) {
        var DEFAULT_SIZE = 25, size, filters = [], post_filters = [];

        if (params == null) {
          params = {};
        }

        /**
         * Set from/size for given query and params
         *
         * @param {Object} query
         * @param {Object} params
         * @returns {Object}
         */
        function paginate(query, params) {
          var page = params.page || 1;
          var pagesize = size || Number(localStorage.getItem('pagesize')) ||
                         Number(params.max_results) || DEFAULT_SIZE;
          query.size = pagesize;
          query.from = (page - 1) * query.size;
        }

        function buildFilters(params, query) {

          if (params.beforefirstcreated || params.afterfirstcreated) {
            var range = {firstcreated : {}};
            if (params.beforefirstcreated) {
              range.firstcreated.lte = params.beforefirstcreated;
            }

            if (params.afterfirstcreated) {
              range.firstcreated.gte = params.afterfirstcreated;
            }

            query.post_filter({range : range});
          }

          if (params.beforeversioncreated || params.afterversioncreated) {
            var vrange = {versioncreated : {}};
            if (params.beforeversioncreated) {
              vrange.versioncreated.lte = params.beforeversioncreated;
            }

            if (params.afterversioncreated) {
              vrange.versioncreated.gte = params.afterversioncreated;
            }

            query.post_filter({range : vrange});
          }

          if (params.after) {
            var facetrange = {firstcreated : {}};
            facetrange.firstcreated.gte = params.after;
            query.post_filter({range : facetrange});
          }

          if (params.type) {
            var type = {type : JSON.parse(params.type)};
            query.post_filter({terms : type});
          } else {
            // default to only picture types
            query.post_filter({terms : {type : [ 'picture' ]}});
          }

          if (params.urgency) {
            query.post_filter({terms : {urgency : JSON.parse(params.urgency)}});
          }

          if (params.source) {
            query.post_filter({terms : {source : JSON.parse(params.source)}});
          }

          if (params.category) {
            query.post_filter(
                {terms : {'anpa_category.name' : JSON.parse(params.category)}});
          }

          if (params.desk) {
            query.post_filter(
                {terms : {'task.desk' : JSON.parse(params.desk)}});
          } else {
            // default desk to verified images
            // TODO: lookup desk by name here
            // query.post_filter({terms: {'task.desk':
            // ['55b0b4c788f929738fa5d069']}});
          }

          if (params.stage) {
            query.post_filter(
                {terms : {'task.stage' : JSON.parse(params.stage)}});
          }

          if (params.state) {
            query.post_filter({terms : {'state' : JSON.parse(params.state)}});
          }

          // add filemeta and verification filters
          if (params.make) {
            query.post_filter(
                {terms : {'filemeta.Make' : JSON.parse(params.make)}});
          }
          if (params.capture_location) {
            query.post_filter({
              terms : {
                'verification.stats.izitru.location' :
                    JSON.parse(params.capture_location)
              }
            });
          }
          if (params.izitru) {
            query.post_filter({
              terms : {
                'verification.stats.izitru.verdict' : JSON.parse(params.izitru)
              }
            });
          }
          if (params.vpp_tag) {
            query.post_filter(
                {terms : {'vpp_tag' : JSON.parse(params.vpp_tag)}});
          }
          if (params.original_source) {
            query.post_filter({
              terms :
                  {'original_source' : JSON.parse(params.original_source)}
            });
          }
        }

        /**
         * Get criteria for given query
         */
        this.getCriteria = function getCriteria(withSource) {
          var search = params;
          var sort = getSort();
          var criteria = {
            query : {filtered : {filter : {and : filters}}},
            sort : [ _.zipObject([ sort.field ], [ sort.dir ]) ]
          };

          if (post_filters.length > 0) {
            criteria.post_filter = {'and' : post_filters};
          }

          paginate(criteria, search);

          if (search.q) {
            criteria.query.filtered.query = {
              query_string : {
                query : search.q,
                lenient : false,
                default_operator : 'AND'
              }
            };
          }

          if (withSource) {
            criteria = {source : criteria};
            if (search.repo) {
              criteria.repo = search.repo;
            }
          }

          return criteria;
        };

        /**
         * Add filter to query
         *
         * @param {Object} filter
         */
        this.filter = function addFilter(filter) {
          filters.push(filter);
          return this;
        };

        this.post_filter = function addPostFilter(filter) {
          post_filters.push(filter);
          return this;
        };

        /**
         * Set size
         *
         * @param {number} _size
         */
        this.size = function setSize(_size) {
          size = _size != null ? _size : size;
          return this;
        };

        // do base filtering
        if (params.spike) {
          this.filter({term : {state : 'spiked'}});
        } else {
          this.filter({not : {term : {state : 'spiked'}}});
        }

        buildFilters(params, this);
      }

      /**
       * Start creating a new query
       *
       * @param {Object} params
       */
      this.query = function createQuery(params) { return new Query(params); };

      this.markViewed = function(item) {
        if (item && !item.viewed) {
          var item_clone = _.clone(item);
          item_clone._links.self.href =
              item_clone._links.self.href.replace('search/', 'archive/');
          item_clone._links.self.title = 'Archive';
          api('archive').save(item_clone, {'viewed' : true});
          item.viewed = true;
        }
      };

    }
]);
