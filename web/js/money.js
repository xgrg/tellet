function openMoneyModal() {
    $('#moneyAddModal input#textbox').val('')
    $('#moneyAddModal input#desc').val('')
    $('#moneyAddModal input#amount').val('')
  
    options = ['Roxane', 'Maison', 'Poules', 'Loisirs', 'Voiture', 'Alimentation', 'Piscine', 'Divers'];
    html = '';
    options.forEach(function(v) {
      html += '<option value="' + v + '">';
    });
  
    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
    var yyyy = today.getFullYear();
  
    today = yyyy+ mm + dd;
  
    $('#moneyAddModal input#date').val(today)
  
    $('#moneyAddModal datalist#label').html(html)
    $('#moneyAddModal').modal('show');
  }
  


  function update_money_list() {
    $.ajax({
      type: "POST",
      url: 'todo',
      data: {
        'action': 'show'
      },
      dataType: 'html',
      success: function(data) {
        console.log(data)
        $("class").html(data)
      }
    })
  }
  
  function add_to_money_list() {
    what = $("#moneyAddModal input#desc").val();
    amount = parseInt($("#moneyAddModal input#amount").val());
    label = $("#moneyAddModal input#textbox").val();
    date = $("#moneyAddModal input#date").val();
    what = what + ";" + amount + ";" + label + ";" + date;
    console.log('add ' + what);
    data = {
      "what": what,
      "to": 'money'
    }
  
    $.ajax({
      type: "POST",
      url: '/add',
      data: data,
      dataType: 'json',
      success: function(data) {
        console.log(data)      
        if (data == false)
          $('#notfoundModal').modal('show');
        else
          update_money_list();
        return true;
      },
      error: function(data) {
        console.log(data);
      }
    });
  }
  