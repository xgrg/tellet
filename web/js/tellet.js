function validate_ed(n) {

  if (n.length != 8)
    return false;
  dd = parseInt(n[0]) * 10 + parseInt(n[1]);
  mm = parseInt(n[2]) * 10 + parseInt(n[3]);
  yyyy = parseInt(n[4]) * 1000 + parseInt(n[5]) * 100 + parseInt(n[6]) * 10 + parseInt(n[7]);
  console.log(String(dd) + ";" + String(mm) + ";" + String(yyyy));
  date = new Date(String(yyyy) + ';' + String(mm) + ';' + String(dd));
  console.log(date);
  d = new Date();
  if (isNaN(date) == true | date - d < 0)
    return false;
  else
    return n;
}


function is_modal_invalid(e) {
  parent = $(e).closest('.modal').attr('id');
  console.log(parent)
  val = $('#' + parent + ' #textbox').val();
  test = val == "" | val.indexOf(';') > -1;
  if (parent == "fridgeAddModal") {
    val = $('#' + parent + ' #quantity').val();
    if ($('#current_quantity').is(':visible')) {
      val2 = $('#current_quantity').val()
      test = test | val2 == "" | parseInt(val2) > parseInt(val);
    }
    unit_checked = $('#' + parent + ' #unitunit').is(':checked');
    pc_checked = $('#' + parent + ' #unitpc').is(':checked');
    if (unit_checked) {
      test = test | (val == "" | val < 0);
    } else if (pc_checked & $('#current_quantity').is(':visible')) {
      test = test | (val2 == "" | val2 < 0 | val2 > 100);
    }
  }
  return test
}


function update_quantity(e) {
  html = $("#original_q").html();
  q = parseInt(html.split('/')[1].split(' ')[0]);
  unit = html.split('/')[1].split(' ')[1];
  val = $('#fridgeUseModal input#quantity').val();
  res = q - val;
  if (q - val < 0 | val < 0) {
    $('#fridgeUseModal input#quantity').css('color', 'red');
    $('#fridgeUseModal #use').prop('disabled', true);
    if (q - val < 0)
      res = 0;
    else if (val < 0)
      res = q;
  } else {
    $('#fridgeUseModal input#quantity').css('color', 'black')
    $('#fridgeUseModal #use').prop('disabled', false);
  }
  msg = 'Quantité restante: ' + String(res) + '/' + q + ' ' + unit;
  $("#original_q").html(msg);
}


function click_edit_fridge() {
  what = $(this).parent().parent().attr('data-data')
  $('#fridgeAddModal').attr('data-data', what);
  console.log(what);

  what = what.split(';');
  label = what[0];
  q = what[1];
  original_q = what[2];
  unit = what[3];
  ed = what[4];
  $("input#textbox").val(label);
  $("input#current_quantity").val(q);
  $("input#expirydate").val(ed);

  if (unit == 'pc') {
    $('#unitpc').click();
    $("input#quantity").prop('disabled', true);
  } else if (unit == 'units') {
    $('#unitunit').click();
    $("input#quantity").prop('disabled', false);
    $("input#quantity").val(original_q);
  }
  $('#fridgeAddModal #delete').show();
  $('#current_quantity').show();
  $("#label_current_quantity").show();
  $('#fridgeAddModal #add').text('Sauvegarder')
  $('#fridgeAddModal').modal('show');
}


/* When someone clicks on Use */
function click_use() {
  data = $(this).parent().parent().data('data');
  items = data.split(';');
  $('input#textbox').val(items[0]);
  $('input#quantity').val('');


  $("h5#itemtitle").text(items[0]);
  msg = 'Quantité restante: ' + items[1] + '/' + items[1] + ' ' + items[3];
  $("#original_q").html(msg);
  //$("#quantity").val(items[1]);
  $("#fridgeUseModal #quantity").prop('disabled', false);

  $('#fridgeUseModal').attr("data-data", data);
  $('#fridgeUseModal #use').prop('disabled', true);
  $('#fridgeUseModal input#flexSwitchCheckDefault').prop('checked', false);
  $('#fridgeUseModal').modal('show');
}


function add_to_fridge(then) {
  dest = then;
  if (then == "shopping")
    dest = 'fridge';

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
    $.ajax({
      type: "POST",
      url: action,
      data: data,
      dataType: 'json',
      success: function(data) {
        console.log(data)
        if (data == false)
          $('#notfoundModal').modal('show');
        else {
          update_list(then);
          if (then == 'shopping')
            call_action('/shopping', what.split(';')[0], 'bought');
        }
        return true;
      },
      error: function(data) {
        console.log(data);
      }
    });
  }
}


function update_list(id) {
  $.ajax({
    type: "POST",
    url: id,
    data: {
      'action': 'show'
    },
    dataType: 'html',
    success: function(data) {
      console.log(data)
      $("div#itemlist").html(data)
      if (id == 'fridge' | id == 'pharmacy') {
        $("#itemlist").on('click', "span.bg-success", click_use);
        $("#itemlist").on('click', "span.bg-danger", click_edit_fridge);
      } else if (id == 'shopping') {
        $("#itemlist").on('click', "span.bg-success", click_bought);
        $("#itemlist").on('click', "span.bg-danger", click_edit_shopping);
      }
      else if (id == 'todo') {
        $("#itemlist").on('click', "span.bg-danger", click_edit_shopping);
        $("#itemlist").on('click', "span.bg-success", click_done);
      }
    }
  })
}


function call_action(url, what, action, then) {
  $.ajax({
    type: "POST",
    url: url,
    dataType: 'json',
    data: {
      "what": what,
      "action": action
    },
    success: function(data) {
      console.log(data)
      if (data[0] == false) {
        $('p#errormsg').html(data[1]);
        $('#notfoundModal').modal('show');
        return true;
      } else {
        html = data[1];
        console.log(data)
        $("div#itemlist").html(html)
        if (then == "shopping") {
          $("#itemlist").on('click', "span.bg-success", click_bought);
          $("#itemlist").on('click', "span.bg-danger", click_edit_shopping);
        } else if (then == "fridge" | then == 'pharmacy') {
          $("#itemlist").on('click', "span.bg-success", click_use);
          $("#itemlist").on('click', "span.bg-danger", click_edit_fridge);
        } else if (then == "todo") {
          $("#itemlist").on('click', "span.bg-success", click_done);
          $("#itemlist").on('click', "span.bg-danger", click_edit_shopping);
        }
        return true;
      }
    },
    error: function(data) {
      console.log(data);
    }
  });
}


function use_fridge(dest) {
  item = $("#fridgeUseModal input#textbox").val();
  used_q = parseInt($("#fridgeUseModal input#quantity").val());
  html = $("#original_q").html();
  original_q = parseInt(data.split(';')[2]);
  unit = data.split(';')[3];
  ed = data.split(';')[4];

  q = parseInt(html.split('/')[1].split(' ')[0]);
  unit = html.split('/')[1].split(' ')[1];
  what = item + ';' + String(q - used_q) + ';' + String(original_q) + ';' + unit + ';' + ed;
  item = $("#fridgeUseModal").attr('data-data');
  $("#fridgeUseModal").attr('data-data', what);

  $.ajax({
    type: "POST",
    url: "/edit",
    data: {
      "what": what,
      "to": dest,
      "item": item
    },
    dataType: 'json',
    success: function(data) {
      if (data[0] == false) {
        $('#errormsg').html('Erreur');
        $('#notfoundModal').modal('show');
        return true;
      } else {
        html = data[1];
        $("div#itemlist").replaceWith(html)
        $("span.bg-danger").click(click_edit_fridge);
        $("span.bg-success").click(click_use);
        reshop = $('#fridgeUseModal input#flexSwitchCheckDefault').is(':checked');
        if (reshop == true) {
          console.log('reshop')
          item = what.split(';')[0];
          console.log(what + ';' + item);
          $('#shoppingAddModal input#textbox').val(item)
          $('#shoppingAddModal button#delete').hide();
          $('#shoppingAddModal #add').click(function() {
            add_to_shopping_list('shopping', dest)
          });
          $('#shoppingAddModal').modal('show');
        }
        return true;
      }
    },
    error: function(data) {
      console.log(data);
    }
  });
}


/* When someone clicks on Bought */
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

  $("#fridgeAddModal input#textbox").parent().hide();
  $("h5#itemtitle").text(what);
  $('#fridgeAddModal').modal('show');
}


/* When someone clicks on Edit */
function click_edit_shopping() {
  what = $(this).parent().parent().text();
  what = what.split('\n')[1].trim();
  console.log(what);
  $('#shoppingAddModal').attr('data-data', what);
  $("#shoppingAddModal input#textbox").val(what);
  $('#shoppingAddModal button#delete').show();
  $('#shoppingAddModal #add').text('Sauvegarder')
  $('#shoppingAddModal').modal('show');
}


function add_to_shopping_list(to, then) {

  // Collecting details from shoppingAddModal
  what = $("#shoppingAddModal input#textbox").val();
  console.log('add ' + what);
  data = {
    "what": what,
    "to": to
  }
  action = '/add'

  // If delete is visible, it means we're editing; otherwise we're adding
  if ($('#shoppingAddModal button#delete').is(":visible")) {
    item = $("#shoppingAddModal").attr('data-data');

    action = '/edit'
    data = {
      "what": what,
      "to": to,
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
