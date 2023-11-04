/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

'use strict';

$.fn.treestatus = function() {
    return this.each(function() {
        let $treestatus = $(this);

        // Register an on-click handler for each recent changes edit button.
        $('.recent-changes-edit').on("click", function () {
            // Get the `data-target` field for the edit button.
            let targetId = $(this).data('target');

            // Find the target element.
            let targetInput = $('#' + targetId);

            // Toggle the `disabled` property on the element.
            let isDisabled = targetInput.is(':disabled');
            targetInput.prop('disabled', !isDisabled);
        });

        // Hide the initially-hidden log update elements.
        // TODO this draws in a funky way, how to hide elements before this runs?
        $('.log-update-hidden').toggle();

        // Register an on-click handler for each log update edit button.
        $('.log-update-edit').on("click", function () {
            // Toggle the elements from hidden/visible.
            var closest_form = $(this).closest('.log-update-form');
            closest_form.find('.log-update-hidden').toggle();
            closest_form.find('.log-update-visible').toggle();
        });

        // Toggle selected on all trees.
        $('.select-all-trees').on("click", function () {
            $('.tree-select-checkbox').prop('checked', true);
        });
    });
};
