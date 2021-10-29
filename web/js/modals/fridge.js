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

function update_quantity(e) {
  html = $("#original_q").html();

  q = parseInt(html.split('/')[1].split(' ')[0]);
  unit = html.split('/')[1].split(' ')[1];
  val = $('#useModal input#quantity').val();
  res = q - val;
  if (q - val < 0 | val < 0) {
    $('#useModal input#quantity').css('color', 'red');
    $('#useModal #useitem').prop('disabled', true);
    if (q - val < 0)
      res = 0;
    else if (val < 0) {
      res = q;
    }
  } else {
    $('#useModal input#quantity').css('color', 'black')
    $('#useModal #useitem').prop('disabled', false);
  }
  msg = 'Quantité restante: ' + String(res) + '/' + q + ' ' + unit;
  $("#original_q").html(msg);
}

/* When someone clicks on Edit */
function click_edit_fridge() {
  what = $(this).parent().parent().attr('data-data')
  $('#addModalFridge').attr('data-data', what);

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
  $('#deletefromfridge').show();
  $('#current_quantity').show();
  $("#label_current_quantity").show();

  $('#addModalFridge').modal('show');
}


/* When someone clicks on Removed */
function click_removed() {
  item = $(this).parent().parent().parent().parent();
  console.log(item)
  click_badge_fridge(item.attr('data-data'), '/fridge', 'removed');
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
  $("#useModal #quantity").prop('disabled', false);

  $('#useModal').attr("data-data", data);
  $('#useModal #useitem').prop('disabled', true);
  $('#useModal input#flexSwitchCheckDefault').prop('checked', false);
  $('#useModal').modal('show');
}

function saveToFridge(then) {
  what = $("#addModalFridge input#textbox").val();
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
  if (q < 0 | q1 < 0 | q == '' | q1 == ''){
    $('p#errormsg').html('La quantité doit être positive.')
    $('#notfoundModal').modal('show');
  }
  else if (unittype == 'pc' & q1 > 100){
    $('p#errormsg').html('Un pourcentage doit être inférieure à 100.')
    $('#notfoundModal').modal('show');
  } else {
    what = what + ';' + q1 + ';' + q + ';' + unittype + ';' + ed;
    console.log(what);
    action = '/add'
    data = {
      "what": what,
      "to": "fridge",
      "then": then
    }
    if ($('#deletefromfridge').is(":visible")) {
      item = $("#addModalFridge").attr('data-data');

      action = '/edit'
      data = {
        "what": what,
        "to": "fridge",
        "item": item,
        "then": then
      }
    }
    $.ajax({
      type: "POST",
      url: action,
      data: data,
      dataType: 'json',
      success: function(data) {
        console.log(data)
        if (data[0] == false) {
          $('#notfoundModal').modal('show');
          return true;
        } else {
          html = data[1];
          console.log(data)
          $("div#itemlist").html(html)
          $("span.bg-danger").click(click_edit_fridge);
          if (then == 'fridge') {
            $("span.bg-success").click(click_use);
          } else if (then == 'shopping') {
            $("span.bg-success").click(click_bought);
            click_badge_fridge(what.split(';')[0], '/shopping', 'bought');
          }

          return true;
        }
      },
      error: function(data) {
        console.log(data);
      }
    });
  }
}


function click_badge_fridge(what, url, action) {
  if (action == 'remove') {
    console.log(what);
  }
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
        $("span.bg-danger").click(click_edit_fridge);
        $("span.bg-success").click(click_use)
        return true;
      }
    },
    error: function(data) {
      console.log(data);
    }
  });
}


function save_use_fridge() {
  item = $("#useModal input#textbox").val();
  used_q = parseInt($("#useModal input#quantity").val());
  html = $("#original_q").html();
  original_q = parseInt(data.split(';')[2]);
  unit = data.split(';')[3];
  ed = data.split(';')[4];

  q = parseInt(html.split('/')[1].split(' ')[0]);
  unit = html.split('/')[1].split(' ')[1];
  what = item + ';' + String(q - used_q) + ';' + String(original_q) + ';' + unit + ';' + ed;
  item = $("#useModal").attr('data-data');
  $("#useModal").attr('data-data', what);

  $.ajax({
    type: "POST",
    url: "/edit",
    data: {
      "what": what,
      "to": "fridge",
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
        reshop = $('#useModal input#flexSwitchCheckDefault').is(':checked');
        if (reshop == true){
          console.log('reshop')
          item = what.split(';')[0];
          console.log(what + ';' + item);
          $('#buyModal input#textbox').val(item)
          $('#deletefromshopping').hide();
          $('#buyModal button#addtobuy').click(function(){addtobuy('fridge')});
          $('#buyModal').modal('show');
        }
        return true;
      }
    },
    error: function(data) {
      console.log(data);
    }
  });
}

/* When someone clicks on Edit */
function click_edit_shopping() {
  item = $(this);
  what = item.parent().parent().text();
  what = what.split('\n')[1].trim();
  console.log(what);
  $('#buyModal').attr('data-data', what);
  $("input#textbox").val(what);
  $('#deletefromshopping').show();

  $('#buyModal').modal('show');
}

function addtobuy(then){
  what = $("#buyModal input#textbox").val();
  console.log('add '+ what);
  data = {
    "what": what,
    "to": "shopping",
    "then": then
  }
  action = '/add'
  if ($('#deletefromshopping').is(":visible")) {
    item = $("#buyModal").attr('data-data');

    action = '/edit'
    data = {
      "what": what,
      "to": "shopping",
      "item": item,
      "then":then
    }
  }

  $.ajax({
    type: "POST",
    url: action,
    data: data,
    dataType: 'json',
    success: function(data) {
      console.log(data)
      if (data[0] == false) {
        $('#notfoundModal').modal('show');
        return true;
      } else {
        html = data[1];
        console.log(data)
        $("div#itemlist").replaceWith(html)
        if (then == 'fridge') {
          $("span.bg-success").click(click_use);
        } else if (then == 'shopping') {
          $("span.bg-success").click(click_bought);
          click_badge_fridge(what.split(';')[0], '/shopping', 'bought');
        }

        return true;
      }
    },
    error: function(data) {
      console.log(data);
    }
  });
}
