/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

'use strict';

$.fn.treestatus = function() {
    return this.each(function() {
        let $treestatus = $(this);

        // TODO make these things reference Treestatus classes instead.
        let $modal = $('.Treestatus-modal');

        // Clicking the update tree button causes the form modal to display.
        let $updateTreeButton = $treestatus.find('.Treestatus-updateTreeButton');
        $updateTreeButton.on('click', (e) => {
            // TODO test this
            // TODO do we need to calculate display state here too?
            e.preventDefault();
            $modal.css("display", "flex");
        });

        // Clicking the close button will remove the form.
        let $close = $treestatus.find('.StackPage-landingPreview-close');
        $close.on('click', (e) => {
            e.preventDefault();
            $modal.css("display", "none");
        });
    });
};
