var username;
var banTabOpenedOnce = false;

$( function() {
    username = window.location.pathname.split( '/' )[1];

    $( '#followButton' ).click( function() { 
        follow( username );
    });

    $( '#subscriberViewShowAllUsersButton' ).click( function() {
        showActiveUsers = false;
        updateSubscrbierCount();
        reloadSubscribers();
    } );

    $( '#subscriberViewShowActiveUsersButton' ).click( function() {
        showActiveUsers = true;
        updateSubscrbierCount();
        reloadSubscribers();
    } );    

    // bootstrap tab show event
    $( 'a[data-toggle="tab"]' ).on( 'shown.bs.tab', function ( e ) {
        var currentTabName = e.target.getAttribute( "aria-controls" );

        if ( currentTabName === "subscriber" ) {
            if ( $('#subscriber ol a.jscroll-next:last' ).length ) {
                $( '#subscriber ol' ).jscroll({
                    loadingHtml: '<div>...</div>',
                    padding: 20,
                    nextSelector: 'a.jscroll-next:last'
                });
            }
        }

        if ( currentTabName === "subscribedTo" ) {
            if ( $('#subscribedTo ol a.jscroll-next:last' ).length ) {
                $( '#subscribedTo ol' ).jscroll({
                    loadingHtml: '<div>...</div>',
                    padding: 20,
                    nextSelector: 'a.jscroll-next:last'
                });
            }
        }

        if ( currentTabName === "bans" && !banTabOpenedOnce ) {
            banTabOpenedOnce = true;
            $.ajax({
                url : '/api/banhistory/' + username + '/',
                success: function( data ) {
                    $( "#bansTable" ).append( data );
                }
            });  
        }
    } );   
} );

function updateSubscrbierCount() {
    $.ajax({
        url : '/api/subscribercount/' + username,
        data: {
            'active': showActiveUsers
        },
        dataType: "json",
        success: function( data ) {
            $( "#subscriberListTitle" ).text( "Подписчики (" + data.subscriber_count + ")" );
        }
    });    
}

function reloadSubscribers() {
    $.ajax({
        url : '',
        data: {
            'page': 1,
            'list': "subscriber",
            'showActiveUsers': showActiveUsers
        },
        dataType: "html",
        success: function( data ) {
            $( "#subscriber .userListGrid" ).empty();
            $( "#subscriber .userListGrid" ).html( data );
            $( "#subscriber .userListGrid" ).data('jscroll', null);

            if ( $('#subscriber ol a.jscroll-next:last' ).length ) {
                $( '#subscriber ol' ).jscroll({
                    loadingHtml: '<div>...</div>',
                    padding: 20,
                    nextSelector: 'a.jscroll-next:last'
                });
            }
        }
    });    
}