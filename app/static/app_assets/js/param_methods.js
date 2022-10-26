/* jshint esversion: 11 */

const db = new PouchDB('user_pref');
document.getElementById('chkbox_store_user_pref').checked = true;//DEFAULT CHECKED (NEW PARAMETER SETS WILL STORE RESPONSES AS DEFAULTS)
const form = document.getElementById('form_param');
db.info()
  .then(() => {
    load_user_pref();
  });
document.getElementById('chkbox_store_user_pref').addEventListener('change', (event) => {
  if (event.currentTarget.checked) {
    save_user_pref('true');
  } else {
    save_user_pref('false');
  }
});
function load_user_pref() {//POUCHDB FUNCTION
  db.get('user_pref').catch(function (err) {
      //console.log('user pref not stored', err);
    }).then(function (doc) {
      if (doc['user_pref'] === 'false'){//DEFAULT IS 'CHECKED=TRUE' (ONLY CHANGE IF USER OVERRIDE)
          document.getElementById('chkbox_store_user_pref').checked = false;
      }
    }).catch(function (err) {
      // handle any errors - N/A
  });
}
function save_user_pref(checked_option) {//POUCHDB FUNCTION
    console.log("save user pref");
    let pref = {};
    pref._id = 'user_pref';
    db.get('user_pref').then(function (doc) {//GET LATEST REVISION, THEN STORE UPDATED RECORD
        doc._rev = doc._rev; //ADD LATEST REVISION TO JS OBJECT PRIOR TO UPDATING DB
        doc.user_pref = checked_option;
        return db.put(doc);
    }).then(function () {
      return db.get('user_pref');
    }).catch(function (err) {//CREATE IF NOT EXIST
        db.put(pref);
    });
}
function save_local_param(){// POUCHDB FUNCTION
    if (document.getElementById('chkbox_store_user_pref').checked) {
        //const form = document.getElementById('form_param');
        let param = {};
        param._id = 'stored_param';
        Array.from(form.elements).forEach(element => {
            let key = element.name;
            let val = element.value;
            let elem_type = element.type;
            let aryKey = key.split('-');
            let content_section = parseInt(aryKey[0].match(/\d+/));
            if (content_section > 2) {//ONLY CAPTURE BEHAVIOR -> NEURONAL ACTIVITY
                if (elem_type === 'text' && val !== ''){
                    param[key] = [val, elem_type];
                }else if (elem_type === 'radio'){
                    let radio_elem = document.getElementsByName(key);
                    for(let i = 0; i < document.getElementsByName(key).length; i++) {
                        if(document.getElementsByName(key)[i].checked){
                            param[document.getElementsByName(key)[i].id] = [true, elem_type];
                        }
                    }
                }
            }
        });

        let db = new PouchDB('local_default_param'); //NO ACTION IF ALREADY EXISTS
        db.get('stored_param').then(function (doc) {//GET LATEST REVISION, THEN STORE UPDATED RECORD
            param._rev = doc._rev; //ADD LATEST REVISION TO JS OBJECT PRIOR TO UPDATING DB
            return db.put(param);
        }).then(function () {
          return db.get('stored_param');
        }).catch(function (err) {//CREATE IF NOT EXIST
            db.put(param);
        });
    }
    return true;
}

form.addEventListener('submit', function (e) {
    // prevent the form from submitting
    e.preventDefault();

    //VALIDATE FORM

    let complete = save_local_param();//SAVE LOCAL PARAM DEFAULTS (IF SELECTED)

    // submit to the server if the form is valid
    if (complete) {
        console.log('submit form');
        form.submit();
    }
});

// TRIGGERS AFTER PAGE IS FULLY LOADED
window.addEventListener("load", () => {
  const queryString = window.location.search;
  const urlParams = new URLSearchParams(queryString);
  const id = urlParams.get('id');

  if (!urlParams.has('id')) {
      //OVERRIDE DEFAULT VALUES [FROM DB] IF LOCAL PREF SELECTED (ONLY ON NEW PARAMETER SETS)
      let db = new PouchDB('local_default_param');
      db.get('stored_param').then(function (doc) {
        for (let [key, value] of Object.entries(doc)) {
          let elem_value = `${value}`.split(",")[0];
          let elem_type = `${value}`.split(",")[1];
          //REPLACE VALUES FOR INPUT FORM ELEMENTS
          if (elem_type === 'text') {
              document.getElementById(`${key}`).value = elem_value;
          }else if(elem_type === 'radio'){
              document.getElementById(`${key}`).checked = elem_value;
          }
        }
      }).catch(function (err) {
      //console.log("NO DB",err);
      });
  }

});