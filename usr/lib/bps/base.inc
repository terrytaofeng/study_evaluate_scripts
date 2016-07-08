#!/bin/bash




function hex2bin(){
    export LANG=c
    awk '
BEGIN{
  for(i=0;i<256;i++){
     j=sprintf("%02x",i);
     map[toupper(j)]=i;
  }
}
{
 
 len=length($1);
 len=len/2;

 c=toupper($1);
 for(i=1;i<=len;i++){
  printf("%c",map[substr(c,(i-1)*2+1,2)]);
 }
}'

}

function bin2hex(){
    od -t x1 | awk '{for(i=2;i<=NF;i++) printf("%s",toupper($i));}'
}


function html_entity_encode()
{

    local r="
s|\"|&quot;|g;
s|\'|&apos;|g;
s|&|&amp;|g;
s|<|&lt;|g;
s|>|&gt;|g;
";
    sed "$r"
}

function html_entity_decode()
{

    local r="
s|&#34;|\"|g;
s|&#39;|\'|g;
s|&#38;|&|g;
s|&#60;|<|g;
s|&#62;|>|g;
s|&quot;|\"|g;
s|&apos;|\'|g;
s|&amp;|&|g;
s|&lt;|<|g;
s|&gt;|>|g;
";
    sed "$r" 
}

function html_entity_hz_decode()
{
  awk '{
 
 line="";
 l=split($0,a,"");
 for(i=1;i<=l;i++){
  if(a[i]=="\\"){
    n=strtonum("0"a[i+1]""a[i+2]""a[i+3]);
    if(n>0){
      line=line""sprintf("%c",n);
      i+=3;
    }else{
      line=line "" a[i];
    }    
  }else{
    line=line "" a[i];
  }
 }

 print line;

}'
}


#function key [defaultvalue]
function parse_argv(){
  [ "x$1" == "x" ] && return;
  local key=$1
  local dft=$2

  awk -vkey=${key} -vdft=${dft} '
{

     for(i=1;i<=NF;i++){
         idx=index($i,"=");
         if(idx>0){
           a=substr($i,1,idx-1);
           b=substr($i,idx+1);
           if(key == a){
              dft=b;
           }
         }
     }
}
END{
  print dft
  }'
}


function import_html_lib(){
    cat<<EOF
  <link rel="stylesheet" href="/hr/jquery-ui/jquery-ui.css">
  <script src="/hr/jquery.min.js"></script>
  <script src="/hr/jquery-ui/jquery-ui.js"></script>    
EOF
}



#function key [defaultvalue]
function parse_argv(){
  [ "x$1" == "x" ] && return;
  local key=$1
  local dft=$2

  awk -vkey=${key} -vdft=${dft} '
{

     for(i=1;i<=NF;i++){
         idx=index($i,"=");
         if(idx>0){
           a=substr($i,1,idx-1);
           b=substr($i,idx+1);
           if(key == a){
              dft=b;
           }
         }
     }
}
END{
  print dft
  }'
}

function awk_html_lib(){
  echo '
 #ex array,"1nr 2"
 function sort_lines(array,ops,sep,    a_ops,m_ops,i,n,i1,n1,prefix,a,idx){
    n=split(ops,a_ops,"[[:space:]]*")
    for(i=1;i<=n;i++){
        m_ops[gensub("[[:alpha:]]","","g",a_ops[i])] =     gensub("[[:digit:]]","","g",a_ops[i]);
    }
    for(i1 in array){
        n1=split(array[i1],a,sep)
        prefix=""
        for(i=1;i<=n;i++){
            idx=gensub("[[:alpha:]]","","g",a_ops[i])
            if(m_ops[idx] == "n"){
                prefix= prefix sprintf("%010d",a[idx])
            }else if(m_ops[idx] == "r"){
                #TODO
                prefix= prefix sprintf("%-50s",a[idx])
            }else if(m_ops[idx] == "nr" || m_ops[idx] == "rn"){
                prefix= prefix sprintf("%010d",10000000000 - a[idx])
            }else{
                prefix= prefix sprintf("%-50s",a[idx])
            }
        }
        array[i1]= prefix sprintf("%10d",i1)  "##@@##" array[i1]
    }
    asort(array);
    n=length(array);
    for(i=1;i<=n;i++){
        array[i]=gensub(".*##@@##","","",array[i])
    }
    return n;
 }
   
 function url_decode(x, hextab,decoded,i,len,c,c1,c2,code){
   hextab ["0"] = 0; hextab ["8"] = 8;
   hextab ["1"] = 1; hextab ["9"] = 9;
   hextab ["2"] = 2; hextab ["A"] = hextab ["a"] = 10
   hextab ["3"] = 3; hextab ["B"] = hextab ["b"] = 11;
   hextab ["4"] = 4; hextab ["C"] = hextab ["c"] = 12;
   hextab ["5"] = 5; hextab ["D"] = hextab ["d"] = 13;
   hextab ["6"] = 6; hextab ["E"] = hextab ["e"] = 14;
   hextab ["7"] = 7; hextab ["F"] = hextab ["f"] = 15;
   decoded = ""
   i   = 1
   len = length (x)
   while ( i <= len ) {
   c = substr (x, i, 1)
   if ( c == "%" ) {
   if ( i+2 <= len ) {
    c1 = substr (x, i+1, 1)
    c2 = substr (x, i+2, 1)
    if ( hextab [c1] == "" || hextab [c2] == "" ) {
     print "WARNING: invalid hex encoding: %" c1 c2 | "cat >&2"
   } else {
    code = 0 + hextab [c1] * 16 + hextab [c2] + 0
    c = sprintf ("%c", code)
    i = i + 2
   }
   } else {
    print "WARNING: invalid % encoding: " substr ($0, i, len - i)
   }
   } else if ( c == "+" ) {
    c = " "
   }
   decoded = decoded c
   ++i
   }
   return decoded
 
 }

 function path_encode(x){
    return gensub("[[:space:]]","@SPACE@","g",x);
 }

 function path_decode(x){
    return gensub("@SPACE@"," ","g",x);
 }

 function path_format1(x){
    return gensub(".*/","","",x);
 }

 function path_format_by_setting(x, f,d){
    if(OPT_WIDGET_BEAUTY_PATH){
        f=gensub(".*/","","",x);
        d=gensub("/" f,"","",x);
        return gensub(".*/","","",x) "&nbsp;[" d  "]";
    }else{
        return x;
    }
 }

 function ENV(key, value){
    if(key in ENVIRON){
        value=url_decode(ENVIRON[key]);    
    }
    return value;
 }
 function parse_opt_post(dft,i){
 }

function link(m,   k){
    url="?fun="
    if("OPT_FUN" in m){
        url=url m["OPT_FUN"]
    }else{
        url=url OPT_FUN
    }
    for(k in m){
        url=url "&" k "=" m[k]
    }
    return url
 } 

 function link_env(m,   k,a){
    url="?fun="
    if("OPT_FUN" in m){
        url=url m["OPT_FUN"]
    }else{
        url=url OPT_FUN
    }
    for(k in ENVIRON){
        if(k ~/^OPT_/ && k != "OPT_FUN"){
            a[k]=1;
        }
    }    
    for(k in m){
        a[k]=1;
    }

    for(k in a){
        if(k in m){
            url=url "&" k "=" m[k]
        }else{
            url=url "&" k "=" ENVIRON[k]
        }
    }
    url=url "&OPT_T=" systime(); 
    return url
 }

 '

 env|awk -F = '
BEGIN{
    print "function parse_opt(){"
}
/^OPT_/{
    printf("%s=ENVIRON[\"%s\"]\n",$1,$1)

}
END{
    print "parse_opt_post()"
    print "}"
}'


}


function link_env(){
    local codes='
BEGIN{
    getline
    for(i=1;i<=NF;i++){
        n=split($i,a,"=");
        if(n==2){
            ENVIRON[a[1]]=a[2];
        }
    }
    parse_opt();
    print link_env();

}'
  echo $* |  awk  "`gitmap_lib` $codes"

}



#name
function html_widget_head(){
    local name=$1
    cat<<EOF
<div class="widget widget_$name">
EOF
}

function html_widget_tail(){
    echo "</div>"
}

function html_js_form_submit(){
    cat<<EOF
document.getElementById("main_form").submit()
EOF
}




#function name style= onchange= lable= value=
function html_widget_select(){
  
  local name=$1
    local style=`echo $*|parse_argv style|url_decode`
    local onchange=`echo $*|parse_argv onchange|url_decode`
    local lable=`echo $*|parse_argv lable|url_decode`
    local title=`echo $*|parse_argv title|url_decode`
    local value=`echo $*|parse_argv value|url_decode`
    local scripts="";
    if [ "x$onchange" != "x" ];then
        scripts=`$onchange`
    fi
    

        local codes='
BEGIN{
    parse_opt()
    if(name in ENVIRON){
        dft=ENVIRON[name]
    }else{
        dft=value
    }
}  
{
    attr="";
    if(dft==$1){
        attr="selected=\"selected\""
    }
    printf("<option %s value=\"%s\">%s</option>\n",attr,$1,$2)
}
'

    [ "x$lable" != "x" ] && echo "$lable:"
    cat<<EOF
<select name="$name" style="$style" title="$title" onchange='$scripts'>
  <option value="">--</option>
EOF

    awk -F "|" -vname=$name -vvalue=$value "`awk_html_lib` $codes" 
    
    cat<<EOF
 </select>
EOF

}

#function name dft_value lable= title
function html_widget_textfiled(){
  local name=$1
  local title=`echo $*|parse_argv title|url_decode`
  local lable=`echo $*|parse_argv lable|url_decode`
  local rlable=`echo $*|parse_argv rlable|url_decode`
  local dft_value=`echo $*|parse_argv value|url_decode`
  local onchange=`echo $*|parse_argv onchange|url_decode`
  local size=`echo $*|parse_argv size|url_decode`

  local value;
  if env |grep "^OPT_FUN=" > /dev/null;then
    value=`awk -vname=$name 'BEGIN{print ENVIRON[name]}'`
  else
    value=$dft_value
  fi

  local scripts="";
  if [ "x$onchange" != "x" ];then
    scripts=`$onchange`
  fi
  local size_html="";
  [ "x$size" != "x" ] && size_html="size=$size"
  cat<<EOF
$lable<input $size_html id="$name" type="input" name="$name" value="$value" title="$title" onChange='$scripts'>$rlable
EOF

}


#function name dft_value lable= title
function html_widget_checkbox(){
  local name=$1
  local dft_value=$2
  local title=`echo $*|parse_argv title|url_decode`
  local lable=`echo $*|parse_argv lable|url_decode`
  local onclick=`echo $*|parse_argv onclick|url_decode`

  local value;

  if env |grep "^OPT_FUN=" > /dev/null;then
    value=`awk -vname=$name 'BEGIN{print ENVIRON[name]}'`
  else
    value=$dft_value
  fi

  local html_checked;
  if [ "x$value" == "xon" ]  || [ "x$value" == "xON" ];then
    html_checked="checked=\"true\""
  fi

  local scripts="";
  if [ "x$onclick" != "x" ];then
    scripts=`$onclick`
  fi
  cat<<EOF
<input id="$name" type="checkbox" name="$name" $html_checked title="$title" onclick='$scripts'>$lable
EOF

}


#function fun OPT_XXX dft_vale
function load_widget(){
 local fun=$1
 local name=$2
 local dft_value=$3

 local value;
 if env |grep "^OPT_FUN=" > /dev/null;then
    value=`awk -vname=$name 'BEGIN{print ENVIRON[name]}'`
 else
    value=$dft_value
 fi

 if [ "x$value" == "xon" ]  || [ "x$value" == "xON" ];then
   $fun
 fi
 
}


function html_form_head(){

    cat<<EOF
<form id="main_form" action=""  method="get">
EOF

}

function html_form_tail(){
   
    local codes='
BEGIN{
    parse_opt()
    s="OPT_FUN"
    n=split(s,a);
    for(i=1;i<=n;i++) b[a[i]]=1
    for(k in ENVIRON){
        if(k ~/^OPT_/ && !b[k] && k !~/^OPT_WIDGET_/){
          printf("<input type=\"hidden\" id=\"%s\" name=\"%s\" value=\"%s\">",k,k,url_decode(ENVIRON[k]))            
        }
    }

    s=""
    n=split(s,a);
    for(i=1;i<=n;i++){
        k=a[i];
        if(k in ENVIRON){

        }else{
            printf("<input type=\"hidden\" id=\"%s\" name=\"%s\" value=\"\">",k,k)                
        }
    }

}'

   awk  "`awk_html_lib` $codes"

    cat<<EOF
</form>
EOF

}