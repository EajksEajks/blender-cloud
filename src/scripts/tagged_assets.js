/**
 * Support for fetching & rendering assets by tags.
 */
(function($) {
    /* How many nodes to load initially, and when clicked on the 'Load Next' link. */
    const LOAD_INITIAL_COUNT = 5;
    const LOAD_NEXT_COUNT = 3;

    /* Renders a node as a <li> element, returns a jQuery object. */
    function renderAsset(node) {
        let li = $('<li>').addClass('js-tagged-asset');
        let link = $('<a>')
            .attr('href', '/nodes/' + node._id + '/redir')
            .appendTo(li);

        function warnNoPicture() {
            li.addClass('warning');
            link.text('no picture for node ' + node._id);
        }

        if (!node.picture) {
            warnNoPicture();
            return li;
        }

        // TODO: show 'loading' thingy
        $.get('/api/files/' + node.picture)
            .fail(function(error) {
                let msg = xhrErrorResponseMessage(error);
                li.addClass('error').text(msg);
            })
            .done(function(resp) {
                // Render the picture if it has the proper size.
                var show_variation = null;
                if (typeof resp.variations != 'undefined') {
                    for (variation of resp.variations) {
                        if (variation.size != 'm') continue;
                        show_variation = variation;
                        break;
                    }
                }

                if (show_variation == null) {
                    warnNoPicture();
                    return;
                }

                let img = $('<img>')
                    .attr('alt', node.name)
                    .attr('src', variation.link)
                    .attr('width', variation.width)
                    .attr('height', variation.height);
                link.append(img);
            });

        return li;
    }

    function loadNext(ul_element) {
        let $ul = $(ul_element);
        let tagged_assets = ul_element.tagged_assets;  // Stored here by loadTaggedAssets().
        let already_loaded = $ul.find('li.js-tagged-asset').length;

        let load_next = $ul.find('li.js-load-next');

        let nodes_to_load = tagged_assets.slice(already_loaded, already_loaded + LOAD_NEXT_COUNT);
        for (node of nodes_to_load) {
            let li = renderAsset(node);
            load_next.before(li);
        }

        if (already_loaded + LOAD_NEXT_COUNT >= tagged_assets.length)
            load_next.remove();
    }

    $.fn.loadTaggedAssets = function(api_base_url) {
        this.each(function(index, ul_element) {
            // TODO(Sybren): show a 'loading' animation.
            $.get('/api/nodes/tagged/' + ul_element.dataset.assetTag)
                .fail(function(error) {
                    let msg = xhrErrorResponseMessage(error);
                    $('<li>').addClass('error').text(msg).appendTo(ul_element);
                })
                .done(function(resp) {
                    // 'resp' is a list of node documents.
                    // Store the response on the DOM <ul>-element so that we can later render more.
                    ul_element.tagged_assets = resp;

                    // Here render the first N.
                    for (node of resp.slice(0, LOAD_INITIAL_COUNT)) {
                        let li = renderAsset(node);
                        li.appendTo(ul_element);
                    }

                    // Don't bother with a 'load next' link if there is no more.
                    if (resp.length <= LOAD_INITIAL_COUNT) return;

                    // Construct the 'load next' link.
                    let load_next = $('<li>').addClass('js-load-next');
                    let link = $('<a>')
                        .attr('href', 'javascript:void(0);')
                        .click(function() { loadNext(ul_element); return false; })
                        .text('Load next')
                        .appendTo(load_next);
                    load_next.appendTo(ul_element);
                });
        });
    };
}(jQuery));
