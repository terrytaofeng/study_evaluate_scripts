#!/bin/bash
#portal


[ "x$INC_BASE" == "x" ] && INC_BASE="/usr/lib/bps"
source $INC_BASE/base.inc $*


SEP="@-"
SEP1="@,"
SEP_PATH="/"


BD="/var/www/html/data/loginfo"

# loginfo format
# timestamp(second)@category@tag@value
#
#OPT_LOG_FILE
#OPT_LOG_CATEGORY
#OPT_LOG_TAG
#OPT_LOG_VALUE


function log(){
  [ "x$OPT_LOG_FILE" == "x" ] && return;
  awk '
BEGIN{
  OPT_LOG_CATEGORY=ENVIRON["OPT_LOG_CATEGORY"]
  OPT_LOG_TAG=ENVIRON["OPT_LOG_TAG"]
  OPT_LOG_VALUE=ENVIRON["OPT_LOG_VALUE"]


  timestamp=systime();

  if(OPT_LOG_TAG == "SCORE_SAVE"){
    n=split(OPT_LOG_VALUE,a,",");
    for(i=1;i<=int(n/2);i++){
      t=a[i*2-1];
      t=gensub("__BLANK__"," ","g",t);
      v=a[i*2];
      if(t)
        print timestamp "@" OPT_LOG_CATEGORY "@" t "@" v
    }
  }else{
    OPT_LOG_TAG=gensub("@","#AT#","g",OPT_LOG_TAG)

    if(OPT_LOG_TAG){
      print timestamp "@" OPT_LOG_CATEGORY "@" OPT_LOG_TAG "@" OPT_LOG_VALUE
    }
  }

}' >> $OPT_LOG_FILE

}


function message_status(){
  local status=$1
  local message=$2
  [ "x$1" == "x" ] && status="0"

  cat<<EOF
{"status":$status,"message":"$message"}  
EOF

}

function html_log_json(){
  html_response_type "text/html"

  if [ "x$OPT_LOG_FILE" == "x" ] || [ "x$OPT_LOG_TAG" == "x" ];then
    message_status "1" "missing params"
    return;
  fi

  log
  message_status

}

function cat_log_file(){
  local f="$OPT_LOG_FILE"
  [ "x$1" != "x" ] && f=$1

  [ "x$f" == "x" ] && return
  [ ! -f "$f" ] && return

  cat $f|egrep "$OPT_WIDGET_LOG_CATEGORY"
}

function summary_log_file(){
  local f="$OPT_LOG_FILE"
  [ "x$1" != "x" ] && f=$1

  [ "x$f" == "x" ] && return
  [ ! -f "$f" ] && return


  local sort_opt=` awk '
BEGIN{
   OPT_SORT_KEY=ENVIRON["OPT_SORT_KEY"]
   OPT_SORT_TYPE=ENVIRON["OPT_SORT_TYPE"]

   if(!OPT_SORT_KEY || OPT_SORT_KEY == "1"){
   }else{
    opt=" -k " OPT_SORT_KEY " -n "
    if(!OPT_SORT_TYPE){
   #   OPT_SORT_TYPE = "desc"
    }
   }
   if(OPT_SORT_TYPE == "desc"){
    opt=opt " -r ";
   }
   print opt
}'`

  [ "x$OPT_SORT_KEY" == 1 ]


  cat_log_file| awk -F "@" '
{
  VALUE[$4]=$4
}
END{
  printf("#tag@score@total");
  asort(VALUE);
  n=length(VALUE);
  for(i=1;i<=n;i++){
    title=VALUE[i];
    if(title == "") title="empty"
    printf("@%s",title);
  }
  printf("@marks@scores");
  print "";
}'

  cat_log_file| awk -F "@" '

BEGIN{
  SEP=ENVIRON["SEP"]
  OPT_TIMESTAMP_MAX=ENVIRON["OPT_TIMESTAMP_MAX"];
  OPT_TIMESTAMP_MIN=ENVIRON["OPT_TIMESTAMP_MIN"];
  max = int(OPT_TIMESTAMP_MAX);
  min = int(OPT_TIMESTAMP_MIN);
} 
 function valid_mark(m){
  return m == "0" || (int(m) > 0 && int(m) <=10);
 } 


 function getA(array,idx1,idx2,  idx){
  idx = idx1 SEP idx2
  if(idx in array){
    return array[idx];
  }else{
    return 0;
  }
 }

 function setA(array,value,idx1,idx2, idx){
  idx = idx1 SEP idx2
  array[idx] = value;
 }

 function computeY(t_n,t_n_1, t){
  if(t_n_1 == 0){
    return 0;
  }else{
    t = t_n - t_n_1
  }
  if(t < 20*60){
    return 0.8
  }else if(t < 60*60){
    return 0.58
  }else if(t < 60*60*24){
    return 0.44
  }else if(t < 60*60*24*7){
    return 0.26
  }else if(t < 60*60*24*30){
    return 0.23
  }else{
    return 0.21
  }
 }

 function computeN(n,  a){
   a=0.9
   return a + (1-a) * exp(-n) * exp(1);
 }

 function getSpace(t_n,t_n_1, s,i,n){
  if(!t_n_1){
    t_n_1 = firttime
  }
  s="";
  OPT_DIV=3600*24;
  n=int((t_n - t_n_1)/OPT_DIV)
  for(i=0;i<n;i++) s=s "_";
  return s;
 }

 function computeS(s_n_1,n,m_n,t_n,t_n_1,  a,b,N){
    a=(1-computeY(t_n,t_n_1));
    N=computeN(n);
    b=a*N
    return (1-b) * s_n_1 + b * m_n;
 }

 function computeS_current(s,n,t_n, y,a){
  a=0.4
  y=computeY(systime(),t_n)
  return  (1 - (1-y)*a/(n+1))*s
 }

 function computeS_fixed(s,n){
    if(s == 0){
      if(n > 0){
        s -= n;
      }
      if(s < -10){
        s = -10;
      }
      return s;
    }else{
      return s;
    }
 }

{

  if(length(OPT_TIMESTAMP_MAX) > 0){
    if(int($1) > max){
      next;
    }
  }


  if(!firttime) firttime=$1;
  if(valid_mark($4)){
    t_n=int($1);
    m_n=int($4);
    tag=$3

    n = getA(AN,tag) + 1
   
    s_n_1 = getA(AS,tag,n-1)
    t_n_1 = getA(AT,tag,n-1)

    s_n = computeS(s_n_1,n,m_n,t_n,t_n_1)

   # print "#1","tag:" tag  " n:" n " t_n:"t_n " m_n:" m_n " s_n_1:" s_n_1 " t_n_1:"t_n_1 " a :" a " N:"N " b:"b " s_n:"s_n

    setA(AS,s_n,tag,n);
    setA(AT,t_n,tag,n);
    setA(AM,m_n,tag,n)
    setA(AN,n,tag)

  }

  if(length(OPT_TIMESTAMP_MIN) > 0){
    if(int($1) <= min){
      next;
    }
  }

  TAG_TOTAL[$3]++;
  TAG_VALUE[$4]=$4
  TAG_VALUE_TOTAL[$3 "__" $4]++;
}

END{

  asort(TAG_VALUE);
  vn=length(TAG_VALUE);
  for(i in TAG_TOTAL){
    tag=i;
    n=getA(AN,tag);
    t_n=getA(AT,tag,n);
    s=int(getA(AS,tag,n)+0.5);
    total=TAG_TOTAL[i]

    printf("%s@",i);


    s_n = computeS_current(s,n,t_n)
    s_n = int(s_n + 0.5)
    s_n = computeS_fixed(s_n,n);

    printf("%s@",s_n);
    
    #printf("%s@",s)    

    printf("%s",total)
    for(j=1;j<=vn;j++){
      printf("@%s",TAG_VALUE_TOTAL[i "__" TAG_VALUE[j]])
    }

    timeline_s=""
    timeline_m=""
    for(j=1;j<=n;j++){
      t_n=getA(AT,tag,j);
      t_n_1=getA(AT,tag,j-1);
      l=getSpace(t_n,t_n_1);
      s=getA(AS,tag,j);
      s=int(s+0.5)
      timeline_s=timeline_s sprintf("%s%s",l,s == 10 ? "A":s);

      m=getA(AM,tag,j);
      m=int(m+0.5)
      timeline_m=timeline_m sprintf("%s%s",l,m == 10 ? "A":m);

    }
    print "@" timeline_m "@" timeline_s;
  }
}
' | sort -t "@" $sort_opt 

}

function summary_log_timeline(){
  local f="$OPT_LOG_FILE"
  [ "x$1" != "x" ] && f=$1

  [ "x$f" == "x" ] && return
  [ ! -f "$f" ] && return

  cat $f | awk -F @ '
BEGIN{
  OPT_TIMELINE_DIV=ENVIRON["OPT_TIMELINE_DIV"]
  OPT_TIMELINE_DIV=int(OPT_TIMELINE_DIV);
  if(!OPT_TIMELINE_DIV)
    OPT_TIMELINE_DIV=600
}  
{

  p=0;
  if(length(last) > 0 && ($1 - last) > OPT_TIMELINE_DIV){
    p=1
  }

  if(p){
    print last
  }

  last=$1
 
}
END{
  if(length(last) > 0)
    print last
}'
}

function generate_dot_file(){
    cat<<EOF
#style_table
digraph G {
EOF

    summary_log_file| awk -F "@" '
BEGIN{

  OPT_FUN=ENVIRON["OPT_FUN"];
  OPT_LOG_FILE=ENVIRON["OPT_LOG_FILE"];
  OPT_SORT_TYPE=ENVIRON["OPT_SORT_TYPE"];
  OPT_SCORE_MAX=ENVIRON["OPT_SCORE_MAX"];
  OPT_SCORE_MIN=ENVIRON["OPT_SCORE_MIN"];
  max=int(OPT_SCORE_MAX);
  min=int(OPT_SCORE_MIN);
}
{

  d=int($2);
  if(length(OPT_SCORE_MAX) > 0){
    if(d > max){
      next;
    }
  }

  if(length(OPT_SCORE_MIN) > 0){
    if(d < min){
      next;
    }
  }
  print $1
}'

    cat<<EOF
}
EOF
}


function plot_log_file(){
  local f="$OPT_LOG_FILE"
  [ "x$1" != "x" ] && f=$1

  [ "x$f" == "x" ] && return
  [ ! -f "$f" ] && return

  local tmpfile=`mktemp`


  cat "$f" | awk -F @ '
BEGIN{
  OPT_SEARCH_TAG=ENVIRON["OPT_SEARCH_TAG"]
}  
{
  if(OPT_SEARCH_TAG == $3){
    s = -1;
    d=int($4);
    if($4 == "0" || (d > 0 && d <=10) ){
      s=d
    }
    if(s != -1){
      s1=s
      if($3 in SCORCE){
        s1=(SCORCE[$3]/2 + s ) * 2 / 3
      }
      SCORCE[$3]=s1
      print $1,d,int(s1)
    }
  }
}' > $tmpfile

  rm $tmpfile
}



function html_log_view_noargs(){
    html_response_type "text/html"

    cat<<EOF
<html>
<head>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
</head>
<body>
EOF


    find -L  $BD -name "*.loginfo.log" | awk -vBD="$BD" '
{

  href="?fun=html_log_view&OPT_LOG_FILE=" $0
  title=gensub(BD,"","",$0);
  printf("<a href=\"%s\">%s</a><br/>\n",href,title)
}'

    cat<<EOF
</body>
</html>
EOF
}

function html_widget_re_study(){

  html_widget_head re_study

    summary_log_file | awk -F "@" '{print int($2)}'|grep -v "#" |sort -n -u| awk '
BEGIN{
  OPT_FUN=ENVIRON["OPT_FUN"];
  OPT_LOG_FILE=ENVIRON["OPT_LOG_FILE"];
  OPT_SORT_TYPE=ENVIRON["OPT_SORT_TYPE"];
  n=1;
}
{
  lines[n++]=$1
}
END{
  printf("&lt;:");
  for(j=1;j<n;j++){
    i=lines[j]
    href="/gitmap.cgi?fun=html_gitdot&OPT_REPO=LOGINFO&OPT_LOG_FILE=" OPT_LOG_FILE "&OPT_FILE=" OPT_LOG_FILE  "&OPT_SCORE_MAX=" i
    printf("<a href=\"%s\"><span title=\"%s\" class=\"span_tag color%d\">%d</span></a> &nbsp;",href,i,i,i);
  }
  print "<br/>"
  printf("=:");
  for(j=1;j<n;j++){
    i=lines[j]
    href="/gitmap.cgi?fun=html_gitdot&OPT_REPO=LOGINFO&OPT_LOG_FILE=" OPT_LOG_FILE "&OPT_FILE=" OPT_LOG_FILE  "&OPT_SCORE_MAX=" i "&OPT_SCORE_MIN=" i
    printf("<a href=\"%s\"><span title=\"%s\" class=\"span_tag color%d\">%d</span></a> &nbsp;",href,i,i,i);
  }

}'
  html_widget_tail
}

function html_widget_detail(){

    summary_log_file| awk -F "@" '
BEGIN{

  OPT_FUN=ENVIRON["OPT_FUN"];
  OPT_LOG_FILE=ENVIRON["OPT_LOG_FILE"];
  OPT_SORT_TYPE=ENVIRON["OPT_SORT_TYPE"];
  n=0;
  print "<div>"
}
{
  size=60
  if($1 != "#tag"){
    d = int($2);
    printf("<span title=\"%s\" class=\"span_tag color%d\">%s</span>",d,d,$1);
    l = l + length($1)
    if(l >= size ) {
      l = 0;
      print "<br/>"
    }
    n++;
    sum[$2]++;
    total++;
  }
}
END{
  print "</div>";
  print "<div>"
  printf("<span title=\"all\"  >%s</span>:",total);
  for(i=-10;i<=10;i++){
    if(sum[i]){
      printf("<span title=\"%s\"  class=\"color%d\">%s</span> ",i,i,sum[i]);  
    }
  }
  print "</div>"

}'
   
}

function html_widget_detail_timeline(){
  html_widget_head graph_timeline

  summary_log_timeline | awk 'BEGIN{last=0} {print last,$1;last=$1}' | sort -n -r| while read min max;do 
    awk -vmax=$max 'BEGIN{printf("<h4>%s</h4>\n",strftime("%Y-%m-%d %H:%M:%S",max))}'

    export OPT_TIMESTAMP_MAX=$max
    unset OPT_TIMESTAMP_MIN
    cat<<EOF
<div class="timeline_graph_full">`html_widget_detail`</div>    
EOF

    export OPT_TIMESTAMP_MIN=$min
    cat<<EOF
<div class="timeline_graph_add">`html_widget_detail`</div>    
EOF

  done

  html_widget_tail
}



function html_log_view(){
    local F="html_log_view"
    export OPT_FUN=$F

    if [ "x$OPT_LOG_FILE"  == "x" ];then 
      [ ! -d $BD ] && { echo "not found $BD";return; }
      html_log_view_noargs
      return
    fi

     html_response_type "text/html"


     local w1=`cat $OPT_LOG_FILE|awk -F "@" '{if(!m[$2]) printf("%s|%s\n",$2,gensub(".*/","","",$2));m[$2]=1}' | html_widget_select OPT_WIDGET_LOG_CATEGORY lable=category onchange=html_js_form_submit`


     cat<<EOF
<html>
<head>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<script src="/hr/jquery.min.js"></script>
<style type="text/css">
.body{
  float:left;
}

.right_column{
  float:left;
}

.color0{background-color:#ffffff;}
.color1{background-color:#ccffff;}
.color2{background-color:#99ffff;}
.color3{background-color:#66ffff;}
.color4{background-color:#33ffff;}
.color5{background-color:#00ffff;}
.color6{background-color:#00ffcc;}
.color7{background-color:#00ff99;}
.color8{background-color:#00ff66;}
.color9{background-color:#00ff33;}
.color10{background-color:#00ff00;}

.color-1{background-color:#ffccff;}
.color-2{background-color:#ff99ff;}
.color-3{background-color:#ff66ff;}
.color-4{background-color:#ff33ff;}
.color-5{background-color:#ff00ff;}
.color-6{background-color:#ff00cc;}
.color-7{background-color:#ff0099;}
.color-8{background-color:#ff0066;}
.color-9{background-color:#ff0033;}
.color-10{background-color:#ff0000;}

.timeline_graph_full{
  display:none;
}
</style>

<script>
 
  \$(document).ready(function(){
    
    \$(".timeline_graph_add").click(function(){
      \$(".timeline_graph_full").show();
      \$(".timeline_graph_add").hide();
    })  


    \$(".timeline_graph_full").click(function(){
      \$(".timeline_graph_add").show();
      \$(".timeline_graph_full").hide();
    })  

 });

</script>

</head>
<body>
`html_form_head`

<div class="nav">
<input type="hidden" name="fun" value="$OPT_FUN">
<table>
<tr>
 <td>$w1 </td>
 <td> `html_widget_re_study`</td>
</tr>
</table>
</div>


<div>
 <div class="body">
EOF
    summary_log_file | awk -F "@" '
BEGIN{

  OPT_FUN=ENVIRON["OPT_FUN"];
  OPT_LOG_FILE=ENVIRON["OPT_LOG_FILE"];
  OPT_SORT_TYPE=ENVIRON["OPT_SORT_TYPE"];
  if(OPT_SORT_TYPE=="desc"){
    OPT_SORT_TYPE="asc"
  }else{
    OPT_SORT_TYPE="desc"
  }
  getline;

  print "<table>"

  print "<tr>"
  for(i=1;i<=NF;i++){
    href="?fun=" OPT_FUN "&OPT_LOG_FILE=" OPT_LOG_FILE "&OPT_SORT_KEY=" i "&OPT_SORT_TYPE=" OPT_SORT_TYPE;
    printf("<td><a href=\"%s\">%s</a></td>",href,$i);
  }
  print "</tr>"
  n=NF;
}
{

  printf("<tr class=\"color%d\">\n",$2);
  for(i=1;i<=NF;i++){
    printf("<td>%s</td>",$i);
  }
  print "</tr>"

}
END{
  print "</table>"
}'

    cat<<EOF
 </div>

 <div class="right_column">

 `html_widget_detail_timeline` 

 </div>

</div>

`html_form_tail`
</body>
</html>     
EOF

}

 #======================================html index==========================================

 function index_b91f548b_9d1c_495c_99da_3f8439e15bd5()
{
    html_response_type "text/html"


    local m=`_last_month 1`
    cat<<EOF
<html>
<ul>
<li><a href="?fun=html_log_view">html_log_view</a></li>
</ul>
</html>

EOF

}



cgi_index="index_b91f548b_9d1c_495c_99da_3f8439e15bd5";
cgi_functions="
html_log_json
html_log_view
"


#======================================================================================
#bash process system v0.3
#
#bps_type
# bps_final           : not include others
# bps_final_exclude   : not include others and not included by others
# bps_exclude         : not included by others
#======================================================================================
for bbb in ./ /usr/bin;do
    if [ -f $bbb/bps.inc ];then
  source $bbb/bps.inc bps_final_exclude "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9"
  break;
    fi
done

