#!/bin/bash


#add below to bash
#======================================================================================
#bash process system v0.3
#
#bps_type 
# bps_final           : not include others
# bps_final_exclude   : not include others and not included by others
# bps_exclude         : not included by others
#======================================================================================
#for bbb in ./ /usr/bin /home/terry/scripts/;do
#    if [ -f $bbb/bps.inc ];then
#	source $bbb/bps.inc [bps_type] "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9"
#	break;
#    fi
#done


BPS_TYPE=
if [ "x$1" == "xbps_final_exclude" ] || [ "x$1" == "xbps_final" ];then
   BPS_TYPE=final
fi

if [ "x$1" == "xbps_final" ] ||  [ "x$1" == "xbps_final_exclude" ] || [ "x$1" == "xbps_exclude" ];then
    shift
fi

BPS_LIB=/usr/lib/bps/

ARGV_MODULE="";
ARGV_FUNCTION="";
ARGV1="";
ARGV2="";
ARGV3="";
ARGV4="";
ARGV5="";



 function getargs()
{
    local args;

    unset ARGV_MODULE;
    unset ARGV_FUNCTION;
    unset ARGV1;
    unset ARGV2;
    unset ARGV3;
    unset ARGV4;
    unset ARGV5;

    while getopts ":a:b:c:d:e:f:m:" args >& /dev/null|| :
    do
      case $args in
          a)
              ARGV1=$OPTARG;
              ;;
          b)
              ARGV2=$OPTARG;
              ;;
          c)
              ARGV3=$OPTARG;
              ;;
          d)
              ARGV4=$OPTARG;
              ;;
          e)
              ARGV5=$OPTARG;
              ;;
          f)
              ARGV_FUNCTION=$OPTARG;
              ;;
          m)
              ARGV_MODULE=$OPTARG;
              ;;
          *)
              break;
              ;;
      esac
    done

#    [ "x$ARGV_MODULE" == "x" ] && ARGV_MODULE=$EXEC_NAME;
#    [ "x$ARGV1" == "x" ] && ARGV1=$1;
#    [ "x$ARGV2" == "x" ] && ARGV2=$2;
#    [ "x$ARGV3" == "x" ] && ARGV3=$3;
#    [ "x$ARGV4" == "x" ] && ARGV4=$4;
#    [ "x$ARGV5" == "x" ] && ARGV5=$5;

}

 function inc_include(){
  [ ! -d $BPS_LIB ] && return;
  local r=`echo "$*" | sed "s|;||g" | awk '{for(i=1;i<=NF;i++){ printf("/%s.inc",$i); if(i!=NF)printf("|")}}'`  

  local incs=`find -L $BPS_LIB -name "*.inc" -type f | egrep "$r" |sort -u`
  [ "x$incs" != "x" ] &&  source $incs
 }

 function awk_include(){
  [ ! -d $BPS_LIB ] && return; 
  local r=`echo "$*" | sed "s|;||g" | awk '{for(i=1;i<=NF;i++){ printf("/%s.awk",$i); if(i!=NF)printf("|")}}'`  
  local files=`find -L $BPS_LIB -name "*.awk" -type f | egrep "$r" |sort -u`
  [ "x$files" != "x" ] &&  cat $files

 }

 function url_decode(){

   awk '

BEGIN {
 hextab ["0"] = 0; hextab ["8"] = 8;
 hextab ["1"] = 1; hextab ["9"] = 9;
 hextab ["2"] = 2; hextab ["A"] = hextab ["a"] = 10
 hextab ["3"] = 3; hextab ["B"] = hextab ["b"] = 11;
 hextab ["4"] = 4; hextab ["C"] = hextab ["c"] = 12;
 hextab ["5"] = 5; hextab ["D"] = hextab ["d"] = 13;
 hextab ["6"] = 6; hextab ["E"] = hextab ["e"] = 14;
 hextab ["7"] = 7; hextab ["F"] = hextab ["f"] = 15;
}
{
 decoded = ""
 i   = 1
 len = length ($0)
 while ( i <= len ) {
 c = substr ($0, i, 1)
 if ( c == "%" ) {
 if ( i+2 <= len ) {
  c1 = substr ($0, i+1, 1)
  c2 = substr ($0, i+2, 1)
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
 print decoded
}
'
}

 function exec_help()
{


    export exec_help_f=$1

    echo "#======================================================================================";
    echo "#bash process system v0.3"
    echo "#======================================================================================";
    echo
    
    local files;
    local fun;

    if [ "x$1" == "xme" ] || [ "x$1" == "xmodule" ];then
	files=${EXEC_NAME}
	fun=$2
    else
	files=${EXEC_NAMES}
	fun=$1
    fi


    for exec_name_1 in ${files};do
	echo "######################################################################"
	echo "#Modules : ${exec_name_1}"
	cat ${exec_name_1} | gawk -vf="$fun" '
BEGIN{
num=1;
i=0;
}

/^#/{
help[i++]=$0;
}

! /^#/ &&  ! /^function/ {
i=0;
}

/^function/{
if(f==substr($2,1,index($2,"(")-1)||f==""||f==num){
  if(f==""){
    if(i>2)
      i=2;
  }
  print "--------------------------------------------------------------------------------";
  printf("[%d] %s\n",num,$2);
  for(j=0;j<i;j++)
    printf("      %s\n",help[j]);
}
  num++;
  i=0;
}
'
	echo 
    done
}

 #html_response_type mime_type [text/html|text/plain|image/gif|image/jpeg|image/png|audio/midi|audio/wav|application/base64 ...]
 function html_response_type(){
     [ "x$1" == "x" ] && return;
     [ "x$IS_CGI" != "x" ] && echo -e  "Content-type: $1\n";
 
}

#main
if [ "x$1" != "xCHILD_PRCESS_SYSTEM" ];then
    EXEC_NAME=$0
    EXEC_NAMES=$0
    EXEC_COMMAND="$0 $*"
    exec_fun=$1


    cache_cgi_functions=`echo $cgi_functions|awk '{for(i=1;i<=NF;i++) print $i}'`
    cache_cgi_index=$cgi_index

    if [ "x$BPS_TYPE" != "xfinal" ];then
	t1=`realpath $EXEC_NAME`
	t2=`dirname $t1`
	t5=`find $t2 -name "*.sh"|grep -v $t1|sort -u|while read t4;do grep "source.*bbb/bps.inc" $t4|grep -v "exclude"|sed "s|.*|$t4|";done |sort -u`
	for t6 in $t5;do
	    source $t6 CHILD_PRCESS_SYSTEM 
	done
	
	EXEC_NAMES="$EXEC_NAME $t5"
    fi

    [ "x$INC_LIB" != "x" ] && inc_include $INC_LIB

    cgi_functions=`echo $cache_cgi_functions|awk '{for(i=1;i<=NF;i++) print $i}'`
    cgi_index=$cache_cgi_index

    IS_CGI=`echo ${REQUEST_URI}|grep "\.cgi"`;


    if [ "x${IS_CGI}" != "x" ]; then
	STDIN=$(cat)
	if [ -n "${STDIN}" ]; then
	    QUERY_STRING="${STDIN}&${QUERY_STRING}"
	fi
	cgi_function=`echo $QUERY_STRING|grep -i fun|sed "s|.*fun=||;s|&.*||;s|+| |g"`
	cgi_arg1=`echo $QUERY_STRING|grep -i arg1|sed "s|.*arg1=||;s|&.*||;"|url_decode`
	cgi_arg2=`echo $QUERY_STRING|grep -i arg2|sed "s|.*arg2=||;s|&.*||;"|url_decode`
	cgi_arg3=`echo $QUERY_STRING|grep -i arg3|sed "s|.*arg3=||;s|&.*||;"|url_decode`
	cgi_arg4=`echo $QUERY_STRING|grep -i arg4|sed "s|.*arg4=||;s|&.*||;"|url_decode`
	cgi_arg5=`echo $QUERY_STRING|grep -i arg5|sed "s|.*arg5=||;s|&.*||;"|url_decode`
	cgi_arg6=`echo $QUERY_STRING|grep -i arg6|sed "s|.*arg6=||;s|&.*||;"|url_decode`
	cgi_arg7=`echo $QUERY_STRING|grep -i arg7|sed "s|.*arg7=||;s|&.*||;"|url_decode`
	cgi_arg8=`echo $QUERY_STRING|grep -i arg8|sed "s|.*arg8=||;s|&.*||;"|url_decode`
	cgi_arg9=`echo $QUERY_STRING|grep -i arg9|sed "s|.*arg9=||;s|&.*||;"|url_decode`
	cgi_envs=`echo $QUERY_STRING|awk -F "&" '{for(i=1;i<=NF;i++){ if($i~/^OPT_/) printf("%s ",$i)}}'`

	for cgi_env in $cgi_envs;do
            export `echo $cgi_env|url_decode`
	done

	if [ "x${cgi_function}" == "x" ];then
	    if [ "x$cgi_index" != "x" ];then
		${cgi_index}
	    else
		index
	    fi
			    
	elif echo ${cgi_functions} |grep "\<${cgi_function}\>" > /dev/null;then
	    ${cgi_function} "${cgi_arg1}" "${cgi_arg2}" "${cgi_arg3}" "${cgi_arg4}" "${cgi_arg5}" "${cgi_arg6}"
	else
	    html_response_type "text/html"
	    cat<<EOF
<pre>
cgi_function: ${cgi_function}
QUERY_STRING: ${QUERY_STRING}
REQUEST_URI:  ${REQUEST_URI}
</pre>
EOF

	fi
	exit 1;
    fi


    if [ "x$exec_fun" == "x" ];then
	exec_help
    elif [ "x$exec_fun" == "xman" ];then
	exec_help $2 $3 $4
    elif [ "x$exec_fun" == "xhelp" ];then
	exec_help $2 $3 $4
    else
	cat $EXEC_NAMES|grep "^function"|gawk -F '(' '{print $1}'|gawk '{print "@"$2"@"}'|grep  "@${exec_fun}@" > /dev/null
	if [ $? -eq 0 ];then
            shift
            $exec_fun "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9"
	else
            exec_help
	fi
    fi
fi
