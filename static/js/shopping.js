const headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

function loadContents(id, res) {

    console.log(res);
    if (res.length == 0) {
        res = "Liste vide."
        $(id).html(res);
        return
    }
    html = '<ul class="list-group">'
    for (i = 0; i < res.length; i++) {
        what = res[i].what;
        when = res[i].when;
        html += `<li when="${when}" class="list-group-item d-flex justify-content-between align-items-center"> <span id="${when}">${what}</span> <span> <span class="badge bg-danger">Editer</span><span class="badge bg-success">Acheté </span></span></li>`
    }
    html = html + "</ul>"
    $(id).html(html);
}

function openShoppingModal() {
    $('#shoppingAddModal input#textbox').val('')

    opt = ['lait', 'fromage', 'chocolat', 'pains précuits'];
    html = '';
    opt.forEach(function (v) {
        html += '<option value="' + v + '">';
    });
    $('#shoppingAddModal datalist#whattobuy').html(html)
    $('#shoppingAddModal #delete').hide();
    $('#shoppingAddModal #add').text('Ajouter')
    $("#shoppingAddModal h5#itemtitle").text('Ajouter');

    $('#shoppingAddModal #add').prop('disabled', true)
    $('#shoppingAddModal input#textbox').on('input', function (e) {
        $('#shoppingAddModal #add').prop('disabled', is_modal_invalid(e.target))
    })
    $('#shoppingAddModal').modal('show');
}


function clickedBought() {
    when = $(this).parent().parent().attr("when")
    what = $(`#${when}`).text()
    $('#fridgeAddModal').attr('when', when);
    $('#fridgeAddModal').attr('what', what);
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


function clickedEdit() {
    when = $(this).parent().parent().attr("when")
    what = $(`#${when}`).text()
    $('#shoppingAddModal').attr('when', when);
    $('#shoppingAddModal').attr('what', what);
    $("#shoppingAddModal input#textbox").val(what);
    $("#shoppingAddModal h5#itemtitle").text('Editer');
    $("#shoppingAddModal input#textbox").show()
    $('#shoppingAddModal button#delete').show();
    $('#shoppingAddModal #add').prop('disabled', false);
    $('#shoppingAddModal #add').text('Sauvegarder')
    $('#shoppingAddModal').modal('show');
}


function add() {
    data = {
        "what": $("#shoppingAddModal input#textbox").val(),
        "where": "shopping"
    }
    console.log(data);
    url = '/add'

    // If delete is visible, it means we're editing; otherwise we're adding
    if ($('#shoppingAddModal button#delete').is(":visible")) {
        url = '/edit'
        data = {
            "what": $("#shoppingAddModal input#textbox").val(),
            "where": "shopping",
            "when": $("#shoppingAddModal").attr('when')
        }
    }

    options = {
        headers: headers,
        method: "POST",
        body: JSON.stringify(data)
    }

    fetch(url, options).then(res => res.json()).then(function (res) {
        html = `<li when="${res.when}" class="list-group-item d-flex justify-content-between align-items-center"><span id="${res.when}">${res.what}</span> <span> <span class="badge bg-danger">Editer</span><span class="badge bg-success">Acheté </span></span></li>`

        if (url == "/add") { // Adding it to the frontend as well
            if ($("#shoppingList ul").length == 0) {
                $("#shoppingList").html('<ul class="list-group"></ul>')
            }
            $("#shoppingList ul").append(html)
            $("span.bg-danger").click(clickedEdit)
            $("span.bg-success").click(clickedBought)
        }
        else {
            items = $("#shoppingList ul li");

            $(`#${res.when}`).text(res.what)
    
        }
    });
}

function change_add_btn_caption(elt){
  caption = $('#fridgeAddModal #add').text();
  if (caption == 'Ajouter')
    $('#fridgeAddModal #add').text('Acheter (Supprimer de la liste)')
  else 
    $('#fridgeAddModal #add').text('Ajouter')
}

function add_to_fridge() {
    checked = $('#fridgeAddModal input#flexSwitch').is(':checked');
  
    if (!checked) { // just remove it, we do not want to add it to fridge
      what = $("#fridgeAddModal").attr("what");
      when = $("#fridgeAddModal").attr("when");
      remove("#shoppingList", when)

      return
    }
  
  
    // Collecting details from fridgeAddModal
    what = $("#fridgeAddModal input#textbox").val();
    if (what == '' | what.indexOf(';') > -1) {
      $('p#errormsg').html('Intitulé de l\'article invalide.')
      $('#notfoundModal').modal('show');
    }
    q = $("input#quantity").val();
    if ($("input#current_quantity").is(':visible') == true)
      q1 = $("input#current_quantity").val();
    else
      q1 = q;
  
    ed = $("input#expirydate").val(); // skipping date validation
  
    unittype = $('#unittype input:radio:checked').attr('data-value');
    if (q < 0 | q1 < 0 | q == '' | q1 == '') {
      $('p#errormsg').html('La quantité doit être positive.')
      $('#notfoundModal').modal('show');
    } else if (unittype == 'pc' & q1 > 100) {
      $('p#errormsg').html('Un pourcentage doit être inférieure à 100.')
      $('#notfoundModal').modal('show');
    } else {
      what = what + ';' + q1 + ';' + q + ';' + unittype + ';' + ed;
      console.log(what);
      action = '/add'
      data = {
        "what": what,
        "to": dest
      }
  
      // If delete is visible, it means we're editing; otherwise we're adding
      item = undefined;
      if ($('#fridgeAddModal #delete').is(":visible")) {
        item = $("#fridgeAddModal").attr('data-data');
        action = '/edit'
        data = {
          "what": what,
          "to": dest,
          "item": item
        }
      }
  
      if (item != undefined)
        console.log('* Replacing ' + item + ' in ' + dest + ' with ' + what + ' from ' + then);
      else
        console.log('Adding ' + what + ' to ' + dest + ' from ' + then)
  
      // Performing query
      options = {
        headers: headers,
        method: "POST",
        body: JSON.stringify(data)
      }

      fetch(action, options).then(res => res.json()).then(function (res){
        console.log(res)
        if (res == false)
          $('#notfoundModal').modal('show');
        else {
          update_list(then);
          if (then == 'shopping')
            call_action('/shopping', what.split(';')[0], 'bought');
        }
        return true;
      })      
    }
  }
  

function remove(id, when) {
    console.log('Removing from shopping: ')
    data = { when: when}
    options = { headers: headers, method: "POST", body: JSON.stringify(data) }
    fetch("/delete", options).then(function (res) { console.log(res); return res.json(); }).then(function (res) {
        $(`#${res.when}`).parent().remove();   
        items = $(id + " ul li");
        if (items.length == 0) 
            $(id).html("Liste vide.");   
        
    });
}


$(function () {
    $("#openAddModal").click(openShoppingModal);
    $('#shoppingAddModal #add').click(add);
    $('#shoppingAddModal #delete').click(function(){when = $(this).closest('#shoppingAddModal').attr('when'); remove("#shoppingList", when)});

    fetch("/list/shopping", { headers: headers }).then(res => res.json()).then(function (res) {
        loadContents("#shoppingList", res)
        $("span.bg-danger").click(clickedEdit)
        $("span.bg-success").click(clickedBought)
    })

    $('#fridgeAddModal #add').click(function () {
        add_to_fridge();
    });

    $("input#unitpc").click(function () {
        $('#quantity').val(100);
        $('#quantity').prop('disabled', true);
    });

    $("input#unitunit").click(function () {
        $('#quantity').val("");
        $('#quantity').prop('disabled', false);
    });
});