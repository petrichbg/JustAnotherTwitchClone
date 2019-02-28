var showActiveUsers = true;

$( function() {
    
    if ( $('#profileList a.jscroll-next:last' ).length ) {
        $('#profileList').jscroll({
            debug: true,
            loadingHtml: '<div>...</div>',
            padding: 20,
            nextSelector: 'a.jscroll-next:last'
        });
    }
    
    $( "#searchUsersButton" ).click( userSearch );
    
    $( "#searchUsersInput" ).keydown( function ( event ) {
        if ( event.keyCode === 13 ) {
            userSearch();
        }
    } );

    $( "#showAllUsersButton" ).click( function() {
        showActiveUsers = false;
        updateUserCount();
        userSearch();
    });

    $( "#showActiveUsersButton" ).click( function() {
        showActiveUsers = true;
        updateUserCount();
        userSearch();
    });

    updateUserCount();
    userSearch();
} );

function updateUserCount() {
    if ( showActiveUsers ) {
        $.ajax({
            url : '/api/activeusercount/',
            dataType: 'json',
            success: function( data ) {
                userCount = data['user_count'];
                $( "#userCount" ).text( userCount );
            }
        });
    } else {
        $.ajax({
            url : '/api/usercount/',
            dataType: 'json',
            success: function( data ) {
                userCount = data['user_count'];
                $( "#userCount" ).text( userCount );
            }
        });
    }
}

function userSearch() {
     var username = $( "#searchUsersInput" ).val();

    $.ajax({
        url : '',
        data: {
            'username': username,
            'showActiveUsers': showActiveUsers
        },
        dataType: "html",
        success: function( data ) {
            $( "#profileList" ).empty();
            $( "#profileList" ).html( data );
            $( "#profileList" ).data('jscroll', null);

            if ( $('#profileList a.jscroll-next:last' ).length ) {
                $('#profileList').jscroll({
                    debug: true,
                    loadingHtml: '<div>...</div>',
                    padding: 20,
                    nextSelector: 'a.jscroll-next:last'
                });
            }
        }
    });
}