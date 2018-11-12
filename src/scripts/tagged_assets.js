/**
 * Support for fetching & rendering assets by tags.
 */
(function($) {
    $.fn.loadTaggedAssets = function(load_initial_count, load_next_count, has_subscription) {
    	mark_if_public = !has_subscription;
        this.each(function(index, each) {
            let $card_deck_element = $(each)
            $card_deck_element.trigger('pillar:workStart');
            $.get('/api/nodes/tagged/' + $card_deck_element.data('assetTag'))
                .fail(function(error) {
                    let msg = xhrErrorResponseMessage(error);
                    $card_deck_element
                        .append(
                            $('<p>').addClass('bg-danger').text(msg)
                        );
                })
                .done(function(resp) {
                    // 'resp' is a list of node documents.
                    $card_deck_element.append(
                        pillar.templates.Nodes.createListOf$nodeItems(resp, load_initial_count, load_next_count)
                    );
                })
                .always(function() {
                    $card_deck_element.trigger('pillar:workStop');
                });
        });
    };
}(jQuery));
