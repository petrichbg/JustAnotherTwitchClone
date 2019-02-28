$( function() {
    
    if ( $('#streamList a.jscroll-next:last' ).length ) {
        $('#streamList').jscroll({
            debug: true,
            loadingHtml: '<div>...</div>',
            padding: 20,
            nextSelector: 'a.jscroll-next:last'
        });
    }
} );