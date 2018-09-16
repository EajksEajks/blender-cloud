/**
 * Support for fetching & rendering assets by tags.
 */
(function($) {
    /* How many nodes to load initially, and when clicked on the 'Load Next' link. */
    const LOAD_INITIAL_COUNT = 5;
    const LOAD_NEXT_COUNT = 3;

    /* Renders a node as an asset card, returns a jQuery object. */
    function renderAsset(node) {
        let card = $('<a class="card asset card-image-fade pr-0 mx-0 mb-2">')
            .addClass('js-tagged-asset')
            .attr('href', '/nodes/' + node._id + '/redir')
            .attr('title', node.name);

        let thumbnail_container = $('<div class="embed-responsive embed-responsive-16by9">');

        function warnNoPicture() {
            let card_icon = $('<div class="card-img-top card-icon embed-responsive-item">');
            card_icon.html('<i class="pi-' + node.node_type + '">');
            thumbnail_container.append(card_icon);
        }

        if (!node.picture) {
            warnNoPicture();
        } else {
            // TODO: show 'loading' thingy
            $.get('/api/files/' + node.picture)
                .fail(function(error) {
                    let msg = xhrErrorResponseMessage(error);
                    console.log(msg);
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

                    let img = $('<img class="card-img-top embed-responsive-item">')
                        .attr('alt', node.name)
                        .attr('src', variation.link)
                        .attr('width', variation.width)
                        .attr('height', variation.height);
                    thumbnail_container.append(img);
                });
        }

        card.append(thumbnail_container);

        /* Card body for title and meta info. */
        let card_body = $('<div class="card-body py-2 d-flex flex-column">');
        let card_title = $('<div class="card-title mb-1 font-weight-bold">');
        card_title.text(node.name);
        card_body.append(card_title);

        let card_meta = $('<ul class="card-text list-unstyled d-flex text-black-50 mt-auto">');
        card_meta.append('<li>' + node._created + '</li>');
        card_body.append(card_meta);

        /* Video progress and 'watched' label. */
        if (node.view_progress){
            let card_progress = $('<div class="progress rounded-0">');
            let card_progress_bar = $('<div class="progress-bar">');
            card_progress_bar.css('width', node.view_progress.progress_in_percent);
            card_progress.append(card_progress_bar);
            card_body.append(card_progress);

            if (node.view_progress.done){
                let card_progress_done = $('<div class="card-label">WATCHED</div>');
                card_body.append(card_progress_done);
            }
        }

        /* 'Free' ribbon for public assets. */
        if (node.permissions && node.permissions.world){
            card.addClass('free');
        }

        card.append(card_body);

        return card;
    }

    function loadNext(card_deck_element) {
        let $card_deck = $(card_deck_element);
        let tagged_assets = card_deck_element.tagged_assets;  // Stored here by loadTaggedAssets().
        let already_loaded = $card_deck.find('a.js-tagged-asset').length;

        let load_next = $card_deck.find('a.js-load-next');

        let nodes_to_load = tagged_assets.slice(already_loaded, already_loaded + LOAD_NEXT_COUNT);
        for (node of nodes_to_load) {
            let link = renderAsset(node);
            load_next.before(link);
        }

        if (already_loaded + LOAD_NEXT_COUNT >= tagged_assets.length)
            load_next.remove();
    }

    $.fn.loadTaggedAssets = function(LOAD_INITIAL_COUNT, LOAD_NEXT_COUNT) {
        this.each(function(index, card_deck_element) {
            // TODO(Sybren): show a 'loading' animation.
            $.get('/api/nodes/tagged/' + card_deck_element.dataset.assetTag)
                .fail(function(error) {
                    let msg = xhrErrorResponseMessage(error);
                    $('<a>').addClass('bg-danger').text(msg).appendTo(card_deck_element);
                })
                .done(function(resp) {
                    // 'resp' is a list of node documents.
                    // Store the response on the DOM card_deck_element so that we can later render more.
                    card_deck_element.tagged_assets = resp;

                    // Here render the first N.
                    for (node of resp.slice(0, LOAD_INITIAL_COUNT)) {
                        let li = renderAsset(node);
                        li.appendTo(card_deck_element);
                    }

                    // Don't bother with a 'load next' link if there is no more.
                    if (resp.length <= LOAD_INITIAL_COUNT) return;

                    if (LOAD_NEXT_COUNT > 0) {
                        // Construct the 'load next' link.
                        let link = $('<a class="btn btn-link px-5 my-auto">')
                            .addClass('js-load-next')
                            .attr('href', 'javascript:void(0);')
                            .click(function() { loadNext(card_deck_element); return false; })
                            .text('Load more items');
                        link.appendTo(card_deck_element);
                    }
                });
        });
    };
}(jQuery));
