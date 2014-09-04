/*
    (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
    Author: Julian Gonggrijp, j.gonggrijp@uu.nl
*/

(function ($) {
    'use strict';
    var display_panel = function (event) {
        event.preventDefault();
        $('#area_panel').position({
            of: $(event.target),
            my: 'left top',
            at: 'right top',
            collision: 'flip flip'
        }).show();
        $(event.target).attr('fill', 'grey');
    }
    var image = $('#coloring_book_image');
    if (image) {
        image.append($('#svg_source').val());
        var svg = $('svg');
        if (svg.attr('viewBox') == '') {
            // Below, I can't just use svg.attr(...) directly, because
            // that method converts everything to lowercase.
            svg.get(0).setAttribute('viewBox', '0 0 ' + svg.attr('width') + ' ' + svg.attr('height'));
        }
        svg.css('max-height', $(window).height() + 'px');
        svg.css('max-width', $('.navbar').width() + 'px');
        $('path').click(display_panel);
        $('#area_panel').hide();
    }
})(window.jQuery);
