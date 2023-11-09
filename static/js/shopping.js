

function loadContents(id) {
    options = {
        headers: {
            'Accept': 'application/json'
        }
    }
    fetch("/list/shopping", options).then(res => res.json()).then(function (res) {
        console.log(res);
        if (res.length == 0){
            res = "Liste vide."
            $(id).html(res);
            return
        }
        html = '<ul class="list-group">'
        for (i=0 ; i < res.length ; i++){
            what = res[i].what;
            when = res[i].when;
            html += `<li when="${when}" class="list-group-item d-flex justify-content-between align-items-center"> ${what} <span> <span class="badge bg-danger">Editer</span><span class="badge bg-success">Acheté </span></span></li>`
        }        
        html = html + "</ul>" 
        $(id).html(html);    
    })
}

function openShoppingModal() {
    $('#shoppingAddModal input#textbox').val('')
  
    options = ['lait', 'fromage', 'chocolat', 'pains précuits'];
    html = '';
    options.forEach(function(v) {
      html += '<option value="' + v + '">';
    });
    $('#shoppingAddModal datalist#whattobuy').html(html)
    $('#shoppingAddModal #delete').hide();
    $('#shoppingAddModal #add').text('Ajouter')
    $("#shoppingAddModal h5#itemtitle").text('Ajouter');
  
    $('#shoppingAddModal #add').prop('disabled', true)
    $('#shoppingAddModal input#textbox').on('input', function(e) {
      $('#shoppingAddModal #add').prop('disabled', is_modal_invalid(e.target))
    })
    $('#shoppingAddModal').modal('show');
  }

function loadContentsModal(){


}



function click_bought() {
    data = $(this).parent().parent().text();
    console.log(data);
    what = data.split('\n')[1].trim();
    $("#fridgeAddModal input#textbox").val(what);
    $("#fridgeAddModal input#quantity").val("");
    $("#fridgeAddModal input#current_quantity").hide();
    $("#fridgeAddModal #label_current_quantity").hide();
    $("#fridgeAddModal input#expirydate").val("");
    $('#fridgeAddModal #unitpc').click();
    $("#fridgeAddModal #delete").hide()
    $('#fridgeAddModal div.form-switch').show();
    $("#fridgeAddModal input#textbox").parent().hide();
    $("h5#itemtitle").text(what);
    $('#fridgeAddModal').modal('show');
  }
  
  
  function click_edit() {
    what = $(this).parent().parent().text();
    what = what.split('\n')[1].trim();
    console.log(what);
    //$('#shoppingAddModal').attr('when', when);
    $('#shoppingAddModal').attr('what', what;
    $("#shoppingAddModal input#textbox").val(what);
    $("#shoppingAddModal h5#itemtitle").text('Editer');
    $("#shoppingAddModal input#textbox").show()
    $('#shoppingAddModal button#delete').show();
    $('#shoppingAddModal #add').prop('disabled', false);
    $('#shoppingAddModal #add').text('Sauvegarder')
    $('#shoppingAddModal').modal('show');
  }
  
  
  function add(to) {
    what = $("#shoppingAddModal input#textbox").val();
    console.log('add ' + what);
    data = {
      "what": what,
      "to": to
    }
    action = '/add'
  
    // If delete is visible, it means we're editing; otherwise we're adding
    if ($('#shoppingAddModal button#delete').is(":visible")) {
      item = $("#shoppingAddModal").attr('what');
  
      action = '/edit'
      data = {
        "what": what,
        "where": to,
        "item": item
      }
    }
  
    $.ajax({
      type: "POST",
      url: action,
      data: data,
      dataType: 'json',
      success: function(data) {
        console.log(data)
        if (data == false)
          $('#notfoundModal').modal('show');
        else
          update_list(then);
        return true;
      },
      error: function(data) {
        console.log(data);
      }
    });
  }
  


$(function () {
    $("#openAddModal").click(openShoppingModal);


    $("span.bg-danger").click(click_edit)
    $("span.bg-success").click(click_bought)


    $('#shoppingAddModal #add').click(function () {
        add('shopping')
    });

    $('#shoppingAddModal #delete').click(function () {
        item = $(this).closest('#shoppingAddModal').attr('data-data');
        console.log('Removing from shopping: ')
        console.log(item)
        call_action('/shopping', item, 'removed');
    });

    $('#fridgeAddModal #add').click(function () {
        add_to_fridge("shopping");
    });


    $("input#unitpc").click(function () {
        $('#quantity').val(100);
        $('#quantity').prop('disabled', true);
    });

    $("input#unitunit").click(function () {
        $('#quantity').val("");
        $('#quantity').prop('disabled', false);
    });

    loadContents("#shoppingList")
});