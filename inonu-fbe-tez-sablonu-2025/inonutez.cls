\NeedsTeXFormat{LaTeX2e}[1996/12/01]
\ProvidesClass{inonutez}[15/02/2011 BE]

\DeclareOption{openbib}{\PassOptionsToClass{openbib}{report}}
\DeclareOption{draft}{\PassOptionsToClass{draft}{report}}
\DeclareOption{final}{\PassOptionsToClass{final}{report}}
\DeclareOption{openright}{\PassOptionsToClass{openright}{report}}
\DeclareOption{openany}{\PassOptionsToClass{openany}{report}}

\DeclareOption{titlepage}{\ClassWarning{inonutez}{Title page always generated. Option ignored.}}
\DeclareOption{notitlepage}{\ClassWarning{inonutez}{Option 'notitlepage' not available for thesis.}}
\DeclareOption{twoside}{\ClassWarning{inonutez}{Option 'twoside' not available for thesis.}}
\DeclareOption{twocolumn}{\ClassWarning{inonutez}{Option 'twocolumn' not available for thesis.}}
\DeclareOption{landscape}{\ClassWarning{inonutez}{Option 'landscape' not available for thesis.}}
\DeclareOption{legalpaper}{\ClassWarning{inonutez}{Option 'legalpaper' not available for thesis.}}
\DeclareOption{a4paper}{\ClassWarning{inonutez}{Option 'a4paper' not available for this class.}}
\DeclareOption{a5paper}{\ClassWarning{inonutez}{Option 'a5paper' not available for this class.}}
\DeclareOption{executivepaper}{\ClassWarning{inonutez}{Option 'executivepaper' not available.}}
\DeclareOption{b5paper}{\ClassWarning{inonutez}{Option 'b5paper' not available for this class.}}
\DeclareOption{letterpaper}{\ClassWarning{inonutez}{Option 'letterpaper' superfluous. Ignored.}}
\DeclareOption{onecolumn}{\ClassWarning{inonutez}{Option 'onecolumn' superfluous.  Ignored.}}
\DeclareOption{oneside}{\ClassWarning{inonutez}{Option 'oneside' superfluous.  Ignored.}}

%====================================== TEZ DERLEME SEÃƒÆ’Ã¢â‚¬Â¡ENEKLERÃƒâ€Ã‚Â° ======================================
\newif\if@Onluarkali
\newif\if@Ingilizce
\@Ingilizcefalse
\newif\if@Doktora
\@Doktorafalse
\newif\if@Bez
\newif\if@SirtKapak
\@SirtKapakfalse
\newif\if@Bilisim
\newif\if@Avrasya
\newif\if@FenBilimleri
\newif\if@SosyalBilimler
\newif\if@Enerji
\newif\if@LisansustuEgitim
\newif\if@APAStyle
\@APAStyletrue
\@Bezfalse
\DeclareOption{onluarkali}{ \PassOptionsToClass{twoside}{report} \@Onluarkalitrue}
\DeclareOption{ingilizce}{\@Ingilizcetrue}
\DeclareOption{doktora}{\@Doktoratrue}
\DeclareOption{turkce}{\@Ingilizcefalse}
\DeclareOption{yukseklisans}{\@Doktorafalse}
\DeclareOption{karton}{\@Bezfalse}
\DeclareOption{bez}{\@Beztrue}
\DeclareOption{sirtkapak}{\@SirtKapaktrue}
\DeclareOption{bilisim}{\@Bilisimtrue}
\DeclareOption{avrasya}{\@Avrasyatrue}
\DeclareOption{fenbilimleri}{\@FenBilimleritrue}
\DeclareOption{sosyalbilimler}{\@SosyalBilimlertrue}
\DeclareOption{enerji}{\@Enerjitrue}
\DeclareOption{LisansustuEgitim}{\@LisansustuEgitimtrue}
\DeclareOption{apa}{\@APAStyletrue}
\DeclareOption{num}{\@APAStylefalse}

\ProcessOptions

\LoadClass[a4paper,onecolumn,11pt]{report}[1996/10/31]
\RequirePackage{ifthen}
\RequirePackage{xstring}
\RequirePackage{iftex}

% Bu sablon zorunlu olarak XeLaTeX ile derlenmelidir.
% Nedeni: Calibri, Unicode Turkce karakterler ve modern font yonetimi.
\ifXeTeX
  \RequirePackage{fontspec}
  \defaultfontfeatures{Ligatures=TeX}
  % 2025 FBE şablonu Calibri kullanır. Calibri yoksa görsel olarak yakın yedekler kullanılır.
  % Dosya adıyla arama, Linux/fontconfig ikamelerinin Calibri varmış gibi algılanmasını önler.
  \IfFontExistsTF{calibri.ttf}{%
    \setmainfont{calibri.ttf}[BoldFont=calibrib.ttf,ItalicFont=calibrii.ttf,BoldItalicFont=calibriz.ttf]%
    \setsansfont{calibri.ttf}[BoldFont=calibrib.ttf,ItalicFont=calibrii.ttf,BoldItalicFont=calibriz.ttf]%
  }{%
    \IfFontExistsTF{Carlito-Regular.ttf}{%
      \setmainfont{Carlito-Regular.ttf}[BoldFont=Carlito-Bold.ttf,ItalicFont=Carlito-Italic.ttf,BoldItalicFont=Carlito-BoldItalic.ttf]%
      \setsansfont{Carlito-Regular.ttf}[BoldFont=Carlito-Bold.ttf,ItalicFont=Carlito-Italic.ttf,BoldItalicFont=Carlito-BoldItalic.ttf]%
    }{%
      \setmainfont{LiberationSans-Regular.ttf}[BoldFont=LiberationSans-Bold.ttf,ItalicFont=LiberationSans-Italic.ttf,BoldItalicFont=LiberationSans-BoldItalic.ttf]%
      \setsansfont{LiberationSans-Regular.ttf}[BoldFont=LiberationSans-Bold.ttf,ItalicFont=LiberationSans-Italic.ttf,BoldItalicFont=LiberationSans-BoldItalic.ttf]%
    }%
  }%
\else
  \def\InonuTezKullanilanDerleyici{bu derleyici}
  \def\InonuTezKullanilanDerleyiciAciklama{Kullandiginiz derleyici}
  \ifPDFTeX
    \def\InonuTezKullanilanDerleyici{pdfLaTeX/PDFTeXify}
    \def\InonuTezKullanilanDerleyiciAciklama{pdfLaTeX veya PDFTeXify}
  \fi
  \ifLuaTeX
    \def\InonuTezKullanilanDerleyici{LuaLaTeX}
    \def\InonuTezKullanilanDerleyiciAciklama{LuaLaTeX}
  \fi
  \typeout{============================================================}
  \typeout{ HATA: BU TEZ XELATEX ILE DERLENMELIDIR.}
  \typeout{ \InonuTezKullanilanDerleyiciAciklama\space kullanmayiniz.}
  \typeout{ WinEdt: TeX menusunden XeLaTeX seciniz.}
  \typeout{ Komut: xelatex tez.tex}
  \typeout{============================================================}
  \errhelp{Bu tez sablonu Calibri fontu, Unicode Turkce karakterler ve yeni nesil font yonetimi icin XeLaTeX gerektirir. Kullanmakta oldugunuz derleyici uygun degildir. WinEdt'te TeX > XeLaTeX komutunu calistirin. Komut satirinda: xelatex tez.tex}
  \errmessage{\InonuTezKullanilanDerleyici\space kullanmayin - XeLaTeX kullanin}
  \expandafter\stop
\fi
\RequirePackage{fancyhdr}
%\RequirePackage[hang]{caption}
\RequirePackage{calc}
\RequirePackage{appendix}
\usepackage[absolute]{textpos}
\usepackage{lscape}
\RequirePackage{graphicx}
\RequirePackage{color}
\RequirePackage{includex} % Scientific WorkPlace/LyX alt dosyalarinda preamble atlayarak dahil etme destegi
\usepackage{url}
\RequirePackage{booktabs}
\RequirePackage{array}
\RequirePackage{tabularx}
\RequirePackage{multirow}
\RequirePackage{perpage}
\RequirePackage[list=true, listformat=simple]{subcaption}
%\RequirePackage{hyperref}\hypersetup{hidelinks}  % EÃƒâ€Ã…Â¸er baÃƒâ€Ã…Â¸lantÃƒâ€Ã‚Â± stilini devre dÃƒâ€Ã‚Â±Ãƒâ€¦Ã…Â¸Ãƒâ€Ã‚Â± bÃƒâ€Ã‚Â±rakmak istiyorsanÃƒâ€Ã‚Â±z aÃƒÆ’Ã‚Â§abilirsiniz.
\usepackage{scrextend}  % AKC
\usepackage{caption}  % AKC
%========================================= CAPTION SETTINGS =========================================
\DeclareCaptionLabelSeparator{period}{\bf{.} } 				% 2025 kilavuzuna gore etiket nokta ile ayrilir.
\DeclareCaptionLabelFormat{subfigure}{\figurename#1~\thefigure\alph{subfigure}}
\captionsetup[table]{font={normalsize,stretch=1.5},labelfont=bf,labelsep=period,position=top,justification=raggedright,singlelinecheck=false,skip=6pt}
\captionsetup[figure]{font={normalsize,stretch=1.5},labelfont=bf,labelsep=period,position=bottom,justification=centering,skip=6pt} % -12
\subcaptionsetup[figure]{labelformat=subfigure,labelfont=bf,font={normalsize,stretch=1.5},labelsep=period,position=bottom,justification=centering,skip=6pt}

%========================================= EQUATION SETTINGS =========================================


%========================================= ENUMARATE SETTINGS ========================================
\renewcommand\labelitemi{\textbullet} % Calibri metin karakteri; matematik fontu kullanmaz
% \setlist{itemsep=6pt, parsep=6pt, topsep=6pt}
\setlength{\labelsep}{.5em}            % Enumeration  
\setlength{\labelwidth}{1.5em}
\setlength{\leftmargin}{0mm}
\setlength{\leftmargini}{1.25em}
\setlength{\leftmarginii}{2.2em}
\setlength{\leftmarginiii}{2.2em}
\setlength{\leftmarginiv}{2.2em}
\setlength{\leftmarginv}{2.2em}
\setlength{\leftmarginvi}{2.2em}

%======================================= HYPHENATION SETTINGS =======================================
% Heceleme iÃƒÆ’Ã‚Â§in hyphenpenalty deÃƒâ€Ã…Â¸erini kÃƒÆ’Ã‚Â¼ÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â¼ltebilirsiniz. 
% DeÃƒâ€Ã…Â¸er kÃƒÆ’Ã‚Â¼ÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â¼ldÃƒÆ’Ã‚Â¼kÃƒÆ’Ã‚Â§e hecelemek isteyecek, deÃƒâ€Ã…Â¸er bÃƒÆ’Ã‚Â¼yÃƒÆ’Ã‚Â¼kdÃƒÆ’Ã‚Â¼kÃƒÆ’Ã‚Â§e hecelemekten kaÃƒÆ’Ã‚Â§acaktÃƒâ€Ã‚Â±r.
\hyphenpenalty=5000
\exhyphenpenalty=5000
\widowpenalty=5000
\clubpenalty=5000

\def\BolumSagdaKalsin{
  \clearpage
  \if@twoside
    \ifodd
      \c@page
    \else
      \hbox{}
      \thispagestyle{empty}
      %\newpage
      \if@twocolumn
	\hbox{}
	%\newpage
      \fi
    \fi
  \fi
} 

\def\BolumSagdaKalsinNolu{
  \clearpage
  \if@twoside
    \ifodd
      \c@page
    \else
      \hbox{}
      \thispagestyle{empty}
      \newpage
      \if@twocolumn
	\hbox{}
	\newpage
      \fi
    \fi
  \fi
} 

\def\@citex[#1]#2{%
  \let\@citea\@empty
  \@cite{\@for\@citeb:=#2\do
    {\@citea\def\@citea{], [}%
     \edef\@citeb{\expandafter\@firstofone\@citeb\@empty}%
     \if@filesw\immediate\write\@auxout{\string\citation{\@citeb}}\fi
     \@ifundefined{b@\@citeb}{\mbox{\reset@font\bfseries ?}%
       \G@refundefinedtrue
       \@latex@warning
         {Citation `\@citeb' on page \thepage \space undefined}}%
       {\hbox{\csname b@\@citeb\endcsname}}}}{#1}}
\def\citepunct{], [}
\def\citedash{]--[}

\lhead{}
\chead{}
\rhead{}
\lfoot{}
\cfoot{\thepage}
\rfoot{}
\renewcommand{\headrulewidth}{0pt}

\newcommand*{\th@PageNumberBottomCenter}{%
  \fancyhf{}%
  \fancyfoot[C]{\thepage}%
  \fancypagestyle{plain}{%
    \fancyhf{}%
    \fancyfoot[C]{\thepage}%
    \renewcommand{\headrulewidth}{0pt}%
  }%
}

\newcommand*{\th@PageNumberBottomRight}{%
  \fancyhf{}%
  \fancyfoot[R]{\thepage}%
  \fancypagestyle{plain}{%
    \fancyhf{}%
    \fancyfoot[R]{\thepage}%
    \renewcommand{\headrulewidth}{0pt}%
  }%
}

%Heceleme iÃƒÆ’Ã‚Â§in hyphenpenalty deÃƒâ€Ã…Â¸erini kÃƒÆ’Ã‚Â¼ÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â¼ltebilirsiniz. 
%DeÃƒâ€Ã…Â¸er kÃƒÆ’Ã‚Â¼ÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â¼ldÃƒÆ’Ã‚Â¼kÃƒÆ’Ã‚Â§e hecelemek isteyecek, deÃƒâ€Ã…Â¸er bÃƒÆ’Ã‚Â¼yÃƒÆ’Ã‚Â¼kdÃƒÆ’Ã‚Â¼kÃƒÆ’Ã‚Â§e hecelemekten kaÃƒÆ’Ã‚Â§acaktÃƒâ€Ã‚Â±r.
\hyphenpenalty=10000
\exhyphenpenalty=10000
\widowpenalty=10000
\clubpenalty=10000

\newlength{\ChapterUstenBosluk}
\setlength{\ChapterUstenBosluk}{0mm} % 2025 kilavuzu: ana baslik sayfanin en ust satirinda baslar.
\newlength{\UstenBosluk}
\setlength{\UstenBosluk}{0mm}

\newlength{\LoFparskip}     %% List of Figure parskip 08-05-2006
\setlength{\LoFparskip}{0em}

\newlength{\LoTparskip}     %% List of Table parskip 08-05-2006
\setlength{\LoTparskip}{0em}

\newlength{\ToCparskip}     %% Table of Content parskip 08-05-2006
\setlength{\ToCparskip}{0em}

\newif\if@SembolListesiVar  %% Sembol Listesi Olsun mu?
\@SembolListesiVarfalse

\newif\if@KisaltmaListesiVar  %% Kisaltma Listesi Olsun mu?
\@KisaltmaListesiVarfalse

\newif\if@TabloListesiVar   %% Tablo Listesi Olsun mu?
\@TabloListesiVartrue       %% Default = Var

\newif\if@SekilListesiVar   %% Sekil Listesi Olsun mu?
\@SekilListesiVartrue       %% Default = Var

\newif\if@ToCisDotted   %% ToC NoktalÃƒâ€Ã‚Â± / NoktasÃƒâ€Ã‚Â±z
\@ToCisDottedfalse      %% Default = NoktasÃƒâ€Ã‚Â±z

\newif\if@ChapterBoldToC%% ToC da BÃƒÆ’Ã¢â‚¬â€œLÃƒÆ’Ã…â€œM 1-2.. bold mu?
\@ChapterBoldToCfalse   %% Default = Bold DeÃƒâ€Ã…Â¸il

\newif\if@TesekkurVar   %% TeÃƒâ€¦Ã…Â¸ekkÃƒÆ’Ã‚Â¼r var mÃƒâ€Ã‚Â±?
\@TesekkurVarfalse      %% Default = False

\newcommand*{\TabloListesiYok}{\@TabloListesiVarfalse}
\newcommand*{\SekilListesiYok}{\@SekilListesiVarfalse}
\newcommand*{\KisaltmaListesiYok}{\@KisaltmaListesiVarfalse}

\newcommand{\th@StoreIn}[2]{\gdef#1{#2}}  %% Stores the second arg in the command specified by the first arg.

\newcommand*{\yazar}[2]{
    \th@StoreIn{\th@isimsoyisim}{#1 #2}
    \th@StoreIn{\th@soyisimisim}{#2, #1}
}
\newcommand*{\tezyazaradsoyad}{\th@isimsoyisim}

%\newcommand*{\danismani[2]}{
%   \th@StoreIn{\th@danismani}{#1}
%   \th@StoreIn{\th@danismaniuniv}{#2}
%}


\newcommand*{\juriBir}[2]{
  \th@StoreIn{\th@juribir}{#1}
  \th@StoreIn{\th@juribiruniv}{#2}
}

\newcommand*{\juriIki}[2]{
  \th@StoreIn{\th@juriiki}{#1}
  \th@StoreIn{\th@juriikiuniv}{#2}
}

\newcommand*{\juriUc}[2]{
  \th@StoreIn{\th@juriuc}{#1}
  \th@StoreIn{\th@juriucuniv}{#2}
}

\newcommand*{\juriDort}[2]{
  \th@StoreIn{\th@juridort}{#1}
  \th@StoreIn{\th@juridortuniv}{#2}
}

\newcommand*{\juriBes}[2]{
  \th@StoreIn{\th@juribes}{#1}
  \th@StoreIn{\th@juribesuniv}{#2}
}


\newcommand{\tezyoneticisi}[2]{
      \th@StoreIn{\th@TezYoneticisi}{#1}
      \th@StoreIn{\th@TezYoneticisiUniv}{#2}
}

\newcommand{\tezyoneticisiENG}[2]{
      \th@StoreIn{\th@TezYoneticisiENG}{#1}
      \th@StoreIn{\th@TezYoneticisiUnivENG}{#2}
}

\newcommand*{\anabilimdali}[2]{
      \th@StoreIn{\th@AnaBilimDali}{#1}
      \th@StoreIn{\th@Department}{#2}
      }
\newcommand*{\programi}[2]{
      \th@StoreIn{\th@Programi}{#1}
      \th@StoreIn{\th@Programme}{#2}
      }

\newcommand*{\ithaf}[1]{\th@StoreIn{\th@Ithaf}{#1}}

\newcommand*{\unvan}[1]{\th@StoreIn{\th@Unvan}{#1}}
\newcommand*{\EnstituMuduru}[1]{\th@StoreIn{\th@EnstituMuduru}{#1}}
\newcommand*{\etikbeyan}[1]{\th@StoreIn{\th@etikbeyanStash}{#1}}
\newcommand*{\bapdestegi}[1]{\th@StoreIn{\th@bapdestegi}{#1}}
\newcommand*{\kapakyili}[1]{\th@StoreIn{\th@kapakyili}{#1}}
\newcommand*{\kapaksehri}[1]{\th@StoreIn{\th@kapaksehri}{#1}}
\newcommand*{\oy}[1]{\th@StoreIn{\th@oy}{#1}}
\newcommand*{\yonetimkurulukarar}[2]{%
  \th@StoreIn{\th@yonetimkurulutarih}{#1}%
  \th@StoreIn{\th@yonetimkurulukararno}{#2}%
}
\def\th@EnstituMuduru{}
\def\th@etikbeyanStash{}
\def\th@bapdestegi{}
\def\th@kapakyili{\the\year}
\def\th@kapaksehri{MALATYA}
\def\th@oy{oy birliği}
\def\th@yonetimkurulutarih{\dotfill}
\def\th@yonetimkurulukararno{\dotfill}
 
      \if@Bilisim
       \def\th@Enstitu{Bili\c sim Enst\. itüsü}
       \def\th@Institute{Informatics Institute}
       \def\th@Instituteiki{} 
      \fi
      \if@FenBilimleri
       \def\th@Enstitu{Fen Bilimleri Enstitüsü}
       \def\th@Institute{Graduate School of Natural and Applied Sciences}
       \def\th@Instituteiki{}
      \fi
      \if@SosyalBilimler
       \def\th@Enstitu{Sosyal B\. il\. imler Enst\. itüsü}
       \def\th@Institute{Graduate School of Arts and Sciences}
       \def\th@Instituteiki{} 
      \fi
      \if@Enerji
       \def\th@Enstitu{Enerj\. i Enst\. itüsü}
       \def\th@Institute{Institute of Energy}
       \def\th@Instituteiki{} 
      \fi
      \if@Avrasya
       \def\th@Enstitu{Avrasya Yer B\. il\. imler\. i Enst\. itüsü}
       \def\th@Institute{Eurasia Institute of Earth Sciences}
       \def\th@Instituteiki{} 
      \fi
      \if@LisansustuEgitim
       \def\th@Enstitu{Fen Bilimleri Enstitüsü}
       \def\th@Institute{Graduate School of Natural and Applied Sciences}
       \def\th@Instituteiki{} 
      \fi

% \newcommand{\kapak}[1]{\th@StoreIn{\th@Kapak}{#1}}
% \if@Bez
%   \kapak{\th@DisKapak\th@IcKapak\if@Ingilizce \th@IcKapakTurkce\fi \th@onaypage}
% \else
%   \kapak{\th@DisKapak\th@IcKapak\if@Ingilizce \th@IcKapakTurkce\fi \th@onaypage}
% \fi

%AKC: TÃƒÆ’Ã‚Â¼rkÃƒÆ’Ã‚Â§e tezlerde ingilizce iÃƒÆ’Ã‚Â§ kapak da olsun
\newcommand{\kapak}[1]{\th@StoreIn{\th@Kapak}{#1}}
\if@Bez
  \kapak{\th@DisKapak\th@IcKapak\th@onaypage}
\else
  \kapak{\th@DisKapak\th@IcKapak\th@onaypage}
\fi



% Türkçe büyük harf dönüşümü: i -> İ, ı -> I vb.
% \MakeUppercase tek başına Türkçe i/ı dönüşümünü doğru yapmadığı için
% metin önce güvenli biçimde dönüştürülür, sonra büyütülür.
\newcommand*{\th@TrUpper}[1]{%
  \begingroup
  \edef\th@tmpUpper{#1}%
  \StrSubstitute{\th@tmpUpper}{i}{İ}[\th@tmpUpper]%
  \StrSubstitute{\th@tmpUpper}{ı}{I}[\th@tmpUpper]%
  \StrSubstitute{\th@tmpUpper}{ş}{Ş}[\th@tmpUpper]%
  \StrSubstitute{\th@tmpUpper}{ğ}{Ğ}[\th@tmpUpper]%
  \StrSubstitute{\th@tmpUpper}{ü}{Ü}[\th@tmpUpper]%
  \StrSubstitute{\th@tmpUpper}{ö}{Ö}[\th@tmpUpper]%
  \StrSubstitute{\th@tmpUpper}{ç}{Ç}[\th@tmpUpper]%
  \MakeUppercase{\th@tmpUpper}%
  \endgroup
}

% === 2025 Word şablonu yardımcıları ===
\newcommand*{\th@ProgramWithSuffix}{%
  \begingroup
  \edef\th@tmpProgram{\Program}%
  \if@Ingilizce
    \IfEndWith{\th@tmpProgram}{Programme}{\th@tmpProgram}{\th@tmpProgram{} Programme}%
  \else
    \IfEndWith{\th@tmpProgram}{Programı}{\th@tmpProgram}{\th@tmpProgram{} Programı}%
  \fi
  \endgroup
}
\newcommand*{\th@MaybeProgramLine}{%
  \ifthenelse{\equal{\Program}{}}{}{{\th@icKapakFt\bfseries \th@ProgramWithSuffix\par}}%
}
\newcommand*{\th@FullTitle}{\Baslikbir\ifthenelse{\equal{\Baslikiki}{}}{}{ \Baslikiki}\ifthenelse{\equal{\Baslikuc}{}}{}{ \Baslikuc}}
\newcommand*{\th@DrawKapakSerit}[1]{%
  \par\noindent\makebox[0pt][l]{\hspace*{-1in}\hspace*{-\oddsidemargin}{\th@KapakSeritRenk\rule{\paperwidth}{13mm}}}%
  \vspace*{-13mm}%
  \par\noindent\makebox[0pt][l]{\hspace*{-1in}\hspace*{-\oddsidemargin}\parbox[c][13mm][c]{\paperwidth}{\centering{\color{white}\th@kapakSeritFt #1}}}%
  \vspace*{13mm}%
}
% Dış kapaktaki şerit Word şablonundaki gibi sayfanın altına yakın,
% fakat alt kenara yapışmadan yerleştirilir. Bu değer, DOKTORA/YÜKSEK
% LİSANS TEZİ satırı ile şerit arasında yeterli boşluk bırakır.
\newlength{\th@DisKapakSeritY}
\setlength{\th@DisKapakSeritY}{270mm}
\newcommand*{\th@DrawDisKapakSerit}[1]{%
  \begin{textblock*}{\paperwidth}(0mm,\th@DisKapakSeritY)%
    \noindent{\th@KapakSeritRenk\rule{\paperwidth}{13mm}}% şerit kalınlığı
  \end{textblock*}%
  \begin{textblock*}{\paperwidth}(0mm,\th@DisKapakSeritY)%
    \parbox[c][13mm][c]{\paperwidth}{\centering{\color{white}\th@kapakSeritFt #1}}%
  \end{textblock*}%
}
\newcommand*{\th@OnayJuriSatiri}[2]{\textbf{#1.}~#2 & ....................\\[3mm]}

\newcommand*{\th@titleFtSz}{\fontseries{b}\fontsize{11}{13.2}\selectfont}             %% Title Font Boyutu
\newcommand*{\th@titleAnaBilimDaliFtSz}{\fontseries{b}\fontsize{11}{13.2}\selectfont} %% AnabilimdalÃƒâ€Ã‚Â± Font Boyutu
\newcommand*{\th@DestekFtSz}{\fontseries{b}\fontsize{11}{13.2}\selectfont}            %% Destek Font Boyutu
\newcommand*{\th@HdFnt}{\sffamily\selectfont\bfseries}                       %% BaÃƒâ€¦Ã…Â¸lÃƒâ€Ã‚Â±klar KalÃƒâ€Ã‚Â±n (Bold) olacak
\newcommand*{\th@ChSz}{\normalsize\fontsize{14}{16.8}\selectfont}                     %% Chapter Font Boyutu 
\newcommand*{\th@ScSz}{\normalsize\fontsize{11}{13.2}\selectfont}                     %% Section Font Boyutu

\newcommand*{\baslik}[3]{
  \th@StoreIn{\th@baslikbir}{#1}
  \th@StoreIn{\th@baslikiki}{#2}
  \th@StoreIn{\th@baslikuc}{#3}
}


\renewcommand*{\title}[3]{
  \th@StoreIn{\th@Titlebir}{#1}
  \th@StoreIn{\th@Titleiki}{#2}
  \th@StoreIn{\th@Titleuc}{#3}
}
\newcommand*{\tarih}[2]{
      \th@StoreIn{\th@tarih}{#1}
      \th@StoreIn{\th@date}{#2}
      }
\newcommand*{\tarihKucuk}[2]{
      \th@StoreIn{\th@tarihKucuk}{#1}
      \th@StoreIn{\th@dateKucuk}{#2}
      }
\newcommand*{\ogrencino}[1]{\th@StoreIn{\th@ogrencino}{#1}}
\newcommand*{\tezvermetarih}[2]{
  \th@StoreIn{\th@tezvermetarih}{#1}
  \th@StoreIn{\th@submissiondate}{#2}
}
\newcommand*{\tezsavunmatarih}[2]{
  \th@StoreIn{\th@tezsavunmatarih}{#1}
  \th@StoreIn{\th@defencedate}{#2}
}

\newcommand*{\esdanismani}[2]{
   \th@StoreIn{\th@esdanisman}{#1}
   \th@StoreIn{\th@esdanismanuniv}{#2}
}

\newcommand*{\esdanismaniENG}[2]{
   \th@StoreIn{\th@esdanismanENG}{#1}
   \th@StoreIn{\th@esdanismanunivENG}{#2}
}

% 2025 Word şablonu terminolojisi: "Eş Danışman" yerine "İkinci Tez Danışmanı".
% Eski komutlar geriye dönük uyumluluk için korunur.
\newcommand*{\ikincitezdanismani}[2]{\esdanismani{#1}{#2}}
\newcommand*{\ikincitezdanismaniENG}[2]{\esdanismaniENG{#1}{#2}}
\newcommand*{\yapayzekakullanimi}[1]{\th@StoreIn{\th@yapayzekakullanimi}{#1}}
\newcommand*{\yapayzekatablosu}[1]{\th@StoreIn{\th@yapayzekatablosu}{#1}}
\def\th@yapayzekakullanimi{hayir}
\def\th@yapayzekatablosu{}


% ====================== INGILIZCE TURKCE TANIMLAMALAR ================================
\if@Ingilizce
  \if@Doktora
    \def\TezSeviyesi{Ph.D. THESIS}
    \def\TezSeviyesiTR{DOKTORA TEZİ}
    \def\TezSeviyesiENG{DOCTORAL DISSERTATION}
  \else
    \def\TezSeviyesi{M.Sc. THESIS}
    \def\TezSeviyesiTR{YÜKSEK LİSANS TEZİ}
    \def\TezSeviyesiENG{MASTER'S THESIS}
  \fi
  \def\th@EnstituUpper{INONU UNIVERSITY \raisebox{0.4mm}{$\bigstar$} \MakeUppercase{\th@Institute}}
  \def\th@EnstituUpperTR{İNÖNÜ ÜNİVERSİTESİ \raisebox{0.4mm}{$\bigstar$} \MakeUppercase{\th@Enstitu}}
  %\def\th@EnstituUpper{INONU UNIVERSITY $\bigstar$ GRADUATE SCHOOL OF NATURAL AND APPLIED SCIENCES}
  \def\Baslikbir{\th@Titlebir}
  \def\Baslikiki{\th@Titleiki}
  \def\Baslikuc{\th@Titleuc}
  \def\Anabilim{\th@Department}
  \def\AnabilimBaslik{Anabilim Dalı}
  \def\Program{\th@Programme}
  \def\ProgramBaslik{Programı}
  \def\TarihBuyuk{\th@date}
  \def\TarihKucuk{\th@dateKucuk}
  \def\VermeTarihi{\th@submissiondate}
  \def\VermeTarihiBaslik{Tezin Enstitüye Verildiği Tarih}
  \def\SavunmaTarihi{\th@defencedate}
  \def\SavunmaTarihiBaslik{Tezin Savunulduğu Tarih}
  \def\YoneticiBaslik{Tez Danışmanı}
  \def\DanismanBaslik{Tez Danışmanı}
  \def\EsDanismanBaslik{İkinci Tez Danışmanı}
  \def\JuriBaslik{Diğer Jüri Üyeleri}
  \def\EklerinBasligi{APPENDICES}
\else
  \if@Doktora
    \def\TezSeviyesi{DOKTORA TEZİ}
    \def\TezSeviyesiENG{DOCTORAL DISSERTATION}
  \else
    \def\TezSeviyesi{YÜKSEK LİSANS TEZİ}
    \def\TezSeviyesiENG{MASTER'S THESIS}
  \fi
  \def\th@EnstituUpper{İNÖNÜ ÜNİVERSİTESİ \raisebox{0.4mm}{$\bigstar$} \MakeUppercase{\th@Enstitu}}
  \def\th@EnstituUpperENG{INONU UNIVERSITY \raisebox{0.4mm}{$\bigstar$} \MakeUppercase{\th@Institute}} %AKC
  %\def\th@EnstituUpper{INONU UNIVERSITESI $\bigstar$ FEN BILIMLERI ENSTITUSU}
  \def\Baslikbir{\th@baslikbir}
  \def\Baslikiki{\th@baslikiki}
  \def\Baslikuc{\th@baslikuc}
  \def\Anabilim{\th@AnaBilimDali}
  \def\AnabilimBaslik{Anabilim Dalı}
  \def\Program{\th@Programi}
  \def\ProgramBaslik{Programı}
  \def\TarihBuyuk{\th@tarih}
  \def\TarihKucuk{\th@tarihKucuk}
  \def\VermeTarihi{\th@tezvermetarih}
  \def\VermeTarihiBaslik{Tezin Enstitüye Verildiği Tarih}
  \def\SavunmaTarihi{\th@tezsavunmatarih}
  \def\SavunmaTarihiBaslik{Tezin Savunulduğu Tarih}
  \def\YoneticiBaslik{Tez Danışmanı}
  \def\DanismanBaslik{Tez Danışmanı}
  \def\EsDanismanBaslik{İkinci Tez Danışmanı}
  \def\JuriBaslik{Diğer Jüri Üyeleri}
  \def\EklerinBasligi{EKLER}
\fi
%====================== BIBTEX ICIN TANIMALAMALAR ========================================
\if@Ingilizce
  \def\baglac{and}
  \def\etal{et al.}
  \def\duzenciler{(editors)}
  \def\duzenci{(editor)}
  \def\duzenleyen{editor}
  \def\surum{edition}
  \def\cilt{volume}
  \def\kisasayi{no.}
  \def\sayi{number}
  \def\ssayfa{pp.}
  \def\sayfa{p.}
  \def\bolum{chapter}
  \def\teknikrapor{Technical Report}
  \def\yuksektezi{Master's thesis}
  \def\doktoratezi{Ph.D. thesis}
\else
  \def\baglac{ve}
  \def\etal{ve diğerleri}
  \def\duzenciler{(düzenleyenler)}
  \def\duzenci{(düzenleyen)}
  \def\duzenleyen{düzenleyen}
  \def\surum{sürüm}
  \def\cilt{cilt}
  \def\kisasayi{sayi}
  \def\sayi{sayi}
  \def\ssayfa{s.}
  \def\sayfa{s.}
  \def\bolum{bölüm}
  \def\teknikrapor{Teknik Rapor}
  \def\yuksektezi{{{(Yüksek Lisans Tezi)}}}
  \def\doktoratezi{{ {(Doktora Tezi)}}}
\fi

%====================== UZUNLUKLA Ãƒâ€Ã‚Â°LGÃƒâ€Ã‚Â°LÃƒâ€Ã‚Â° TANIMALAMALAR ========================================
%\newlength{\kurumboyu}
\newlength{\kaydirmaboyuTR}
\newlength{\kaydirmaboyuENG}

\if@Bilisim
  \setlength{\kaydirmaboyuTR}{80pt}
  \setlength{\kaydirmaboyuENG}{50pt}
\fi
\if@Avrasya
  \setlength{\kaydirmaboyuTR}{40pt}
  \setlength{\kaydirmaboyuENG}{20pt}
\fi
\if@FenBilimleri
  \setlength{\kaydirmaboyuTR}{60pt}
  \setlength{\kaydirmaboyuENG}{20pt}
\fi
\if@SosyalBilimler
  \setlength{\kaydirmaboyuTR}{30pt}
  \setlength{\kaydirmaboyuENG}{20pt}
\fi
\if@Enerji
  \setlength{\kaydirmaboyuTR}{60pt}
  \setlength{\kaydirmaboyuENG}{50pt}
\fi
\if@LisansustuEgitim
  \setlength{\kaydirmaboyuTR}{30pt}
  \setlength{\kaydirmaboyuENG}{50pt}
\fi

\newlength{\defbaselineskip}
\setlength{\defbaselineskip}{\baselineskip}
%%\setlinespacing --> #1 * \defbaselineskip iÃƒâ€¦Ã…Â¸lemini gerÃƒÆ’Ã‚Â§ekleÃƒâ€¦Ã…Â¸tiriyor
\newcommand{\setlinespacing}[1]{\setlength{\baselineskip}{#1\defbaselineskip}}         
\newcommand{\doublespacing}{\setlength{\baselineskip}{2.0\defbaselineskip}}            %%\doublespacing = 2*\defbaselineskip
\newcommand{\singlespacing}{\setlength{\baselineskip}{\defbaselineskip}}                %%\singlespacing = 1*\defbaselineskip
\newcommand{\oneandonehalf}{\setlength{\baselineskip}{1.5\defbaselineskip}}            %%\oneandonehalf = 1.5*\defbaselineskip
\newcommand{\LoFspacing}{\oneandonehalf}
\newcommand{\LoTspacing}{\oneandonehalf}
\newcommand{\ToCspacing}{\oneandonehalf}
\newcommand{\Ozetspacing}{\setlinespacing{1.15}}
\newcommand{\Baslikspacing}{\setlength{\baselineskip}{1.3\defbaselineskip}}            %%\Baslikspacing = 1.2*\defbaselineskip 08-05-2006

% 2025 kilavuzuna gore dipnotlar 10 punto ve tek satir aralikli olmalidir.
\renewcommand\footnotesize{\@setfontsize\footnotesize{10}{12}}
\setlength{\footnotesep}{12pt}
\renewcommand\footnoterule{%
  \kern -3pt
  \hrule \@width .5\textwidth \@height .4pt
  \kern 10pt
}
\MakePerPage{footnote}

% Sekil ve tablo altinda verilecek aciklayici notlar 9 punto olmalidir.
\newcommand{\sekilnotu}[1]{\par\vspace{3pt}{\centering\fontsize{9}{10.8}\selectfont #1\par}}
\newcommand{\tablonotu}[1]{\par\vspace{3pt}{\noindent\fontsize{9}{10.8}\selectfont #1\par}}


%
% Sayfa yapÃƒâ€Ã‚Â±sÃƒâ€Ã‚Â± tanÃƒâ€Ã‚Â±mlanÃƒâ€Ã‚Â±yor...
%

\AtBeginDocument{

        \setlength{\voffset}{-5mm}
        \setlength{\hoffset}{0mm}


        \setlength{\oddsidemargin}{-0.4mm}
        \setlength{\evensidemargin}{-0.4mm}

        \setlength{\topmargin}{-0.8mm}
        \setlength{\headheight}{15pt}         %% Sayfa BaÃƒâ€¦Ã…Â¸lÃƒâ€Ã‚Â±Ãƒâ€Ã…Â¸Ãƒâ€Ã‚Â± (NumarasÃƒâ€Ã‚Â±) = 10 mm
        \setlength{\headsep}{0.0mm}             %% Sayfa BaÃƒâ€¦Ã…Â¸lÃƒâ€Ã‚Â±Ãƒâ€Ã…Â¸Ãƒâ€Ã‚Â± ile Sayfa Metni ArasÃƒâ€Ã‚Â± BoÃƒâ€¦Ã…Â¸luk
        \setlength{\textheight}{245mm}


        \setlength{\textwidth}{160mm}
        \setlength{\marginparsep}{0mm}
        \setlength{\marginparwidth}{0mm}
        \setlength{\leftmargini}{1.25em}
        \setlength{\leftmarginii}{2.2em}
        \setlength{\leftmarginiii}{2.2em}
        \setlength{\leftmarginiv}{2.2em}
        \setlength{\leftmarginv}{2.2em}
        \setlength{\leftmarginvi}{2.2em}
        \setlength{\leftmargin}{0mm}
        \setlength{\labelsep}{.5em}
        \setlength{\labelwidth}{1.5em}
        \setlength{\footskip}{15mm} % sayfa no ile metin arasÃƒâ€Ã‚Â± boÃƒâ€¦Ã…Â¸luk


        \setlength{\topskip}{0mm}
        \setlength{\parindent}{1.25cm}
        \setlength{\parskip}{0pt}
        \pagestyle{fancy}
        \markright{}
        \onecolumn
        \raggedbottom
        \normalsize
        \normalfont
        \oneandonehalf
        \setcounter{tocdepth}{2}
        \setcounter{secnumdepth}{4}
        }

\newif\if@OzgecmisSonda
\@OzgecmisSondatrue
\newcommand{\ozgecmissondabasmasin}{\global\@OzgecmisSondafalse}

\AtEndDocument{
  \if@SirtKapak\else
    \if@OzgecmisSonda
      \th@ozgecmispage
    \fi
  \fi
}

\newcommand*{\th@ChapterStyle}{\th@HdFnt\th@ChSz}
\newcommand*{\th@SectionStyle}{\th@HdFnt\th@ScSz}
\newcommand*{\th@SubSectionStyle}{\th@HdFnt\th@ScSz}
\newcommand*{\th@OtherSecHeadStyles}{\th@HdFnt\th@ScSz}

\newcommand*{\th@DoChapCenter}{}
\newcommand*{\th@ChapHead}[1]{\protect\th@ChapterStyle \protect\th@DoChapCenter #1}

\newcommand*{\chapternameToC}{\sffamily\normalsize\selectfont \if@Ingilizce CHAPTER\else BÖLÜM\fi\normalfont}
\newcommand*{\contentsnameToC}{\sffamily\normalsize\selectfont \if@Ingilizce TABLE OF CONTENTS\else İÇİNDEKİLER\fi\normalfont}
\newcommand*{\listtablenameToC}{\sffamily\normalsize\selectfont \if@Ingilizce LIST OF TABLES\else TABLOLAR DİZİNİ\fi\normalfont}
\newcommand*{\listfigurenameToC}{\sffamily\normalsize\selectfont \if@Ingilizce LIST OF FIGURES\else ŞEKİLLER DİZİNİ\fi\normalfont}
\newcommand*{\abstractnameToC}{\sffamily\normalsize\selectfont ABSTRACT\normalfont}
\newcommand*{\onaynameToC}{\sffamily\normalsize\selectfont KABUL VE ONAY\normalfont}
\newcommand*{\ozetnameToC}{\sffamily\normalsize\selectfont ÖZET\normalfont}
\newcommand*{\onsoznameToC}{\sffamily\normalsize\selectfont \if@Ingilizce ACKNOWLEDGEMENTS AND FOREWORD\else TEŞEKKÜR VE ÖNSÖZ\fi\normalfont}
\newcommand*{\ozgecmisnameToC}{\sffamily\normalsize\selectfont \if@Ingilizce CURRICULUM VITAE\else ÖZGEÇMİŞ\fi\normalfont}
\newcommand*{\appendixnameToC}{\sffamily\normalsize\selectfont \if@Ingilizce APPENDICES\else EKLER\fi\normalfont}
\newcommand*{\symbolnameToC}{\sffamily\normalsize\selectfont \if@Ingilizce SYMBOLS AND ABBREVIATIONS\else SİMGELER VE KISALTMALAR DİZİNİ\fi\normalfont}

\newcommand*{\symbolname}{\th@ChapHead{\if@Ingilizce SYMBOLS AND ABBREVIATIONS\else SİMGELER VE KISALTMALAR DİZİNİ\fi}}
\newcommand*{\kisaltmanameToC}{\sffamily\normalsize\selectfont \if@Ingilizce ABBREVIATIONS\else
KISALTMALAR\fi\normalfont}
\newcommand*{\kisaltmaname}{\th@ChapHead{\if@Ingilizce ABBREVIATIONS\else KISALTMALAR\fi}} 

\def\prefacename{\th@ChapHead{\if@Ingilizce ACKNOWLEDGEMENTS AND FOREWORD\else TEŞEKKÜR VE ÖNSÖZ\fi}}%
\def\refname{\th@ChapHead{\if@Ingilizce REFERENCES\else KAYNAKLAR\fi}}%
\def\abstractname{\th@ChapHead{ÖZET}}%
\def\summaryname{\th@ChapHead{ABSTRACT}}%
\def\ozgecmisname{\th@ChapHead{\if@Ingilizce CURRICULUM VITAE\else ÖZGEÇMİŞ\fi}}%
\def\bibname{\th@ChapHead{\if@Ingilizce REFERENCES\else KAYNAKLAR\fi}}%
\def\bibnameToC{\if@Ingilizce REFERENCES\else KAYNAKLAR\fi}%
\def\chaptername{\th@ChapHead{\if@Ingilizce CHAPTER\else BÖLÜM\fi}}%
\def\appendixname{\th@ChapHead{\if@Ingilizce APPENDIX\else EK\fi}}%
\def\contentsname{\th@ChapHead{\if@Ingilizce TABLE OF CONTENTS\else İÇİNDEKİLER\fi}}%
\def\listfigurename{\th@ChapHead{\if@Ingilizce LIST OF FIGURES\else ŞEKİLLER DİZİNİ\fi}}%
\def\listtablename{\th@ChapHead{\if@Ingilizce LIST OF TABLES\else TABLOLAR DİZİNİ\fi}}%
\def\indexname{\th@ChapHead{\if@Ingilizce INDEX\else DİZİN\fi}}%
\def\figurename{\bf \if@Ingilizce Figure\else Şekil\fi}%
\def\tablename{\bf \if@Ingilizce Table\else Tablo\fi}%
\def\partname{\th@ChapHead{\if@Ingilizce PART\else KISIM\fi}}%
\def\glossaryname{\th@ChapHead{\if@Ingilizce DICTIONARY\else TERİMLER SÖZLÜĞÜ\fi}}

\newcommand*{\th@DefTheChapter}{\arabic{chapter}}
\newcommand*{\th@DefTheSection}{\th@DefTheChapter.\arabic{section}}
\newcommand*{\th@DefTheSubsection}{\th@DefTheSection.\arabic{subsection}}
\newcommand*{\th@DefTheSubsubsection}{\th@DefTheSubsection.\arabic{subsubsection}}
\newcommand*{\th@DefTheSubsubsubsection}{\th@DefTheSubsubsection.\arabic{subsubsubsection}}

\renewcommand*{\thechapter}{\th@DefTheChapter}
\renewcommand*{\thesection}{\th@DefTheSection}
\renewcommand*{\thesubsection}{\th@DefTheSubsection}
\renewcommand*{\thesubsubsection}{\th@DefTheSubsubsection}
\newcommand*{\thesubsubsubsection}{\th@DefTheSubsubsubsection}
\setcounter{tocdepth}{2}

\newcommand*{\ToCLineisDotted}{\@ToCisDottedtrue}
\ToCLineisDotted

\renewcommand*\l@part[2]{%
  \ifnum \c@tocdepth >\m@ne
    \addpenalty{-\@highpenalty}%
    \vskip 0.1em \@plus\p@
    \setlength\@tempdima{1.5em}%
    \begingroup
      \parindent \z@ \rightskip \@pnumwidth
      \parfillskip -\@pnumwidth
      \leavevmode \bfseries
      #1\nobreak
       \if@ToCisDotted
       \leaders\hbox{$\m@th\hbox{.}$}
%        \mkern \@dotsep mu\hbox{.}\mkern \@dotsep
%         mu$}
       \fi
      \hfil\nobreak\hb@xt@\@pnumwidth{\hss #2}\par
      \penalty\@highpenalty
    \endgroup
  \fi
}

\renewcommand*\l@chapter[2]{%
  \ifnum \c@tocdepth >\m@ne
    \addpenalty{-\@highpenalty}%
    \vskip 1.0em \@plus\p@
    \setlength\@tempdima{1.5em}%
    \begingroup
      \parindent \z@ \rightskip \@pnumwidth
      \parfillskip -\@pnumwidth
      \leavevmode \bfseries
      #1\nobreak
       \if@ToCisDotted
       \leaders\hbox{$\m@th\hbox{.}$}
%        \mkern \@dotsep mu\hbox{.}\mkern \@dotsep
%         mu$}
       \fi
      \hfil\nobreak\hb@xt@\@pnumwidth{\hss #2}\par
      \penalty\@highpenalty
    \endgroup
  \fi}
  
\def\@tocline#1#2#3#4#5{%
  \vskip 1\p@
  \ifnum #1>\c@tocdepth \else
    \vskip \z@ \@plus.2\p@
    {\leftskip #2\relax \rightskip \@tocrmarg \parfillskip -\rightskip
     \parindent #2\relax\@afterindenttrue
     \interlinepenalty\@M
     \leavevmode
     \@tempdima #3\relax
     \advance\leftskip \@tempdima \null\nobreak\hskip -\leftskip
     {#4}\nobreak
      \if@ToCisDotted
       \leaders\hbox{$\m@th\hbox{.}$}
%        \mkern \@dotsep mu\hbox{.} \mkern\@dotsep
%         mu$}
       \fi
     \hfill
     \nobreak
     \nobreak\hb@xt@\@pnumwidth{\hss #5}
     \par}%
  \fi}

\renewcommand\citepunct{,} %AKC:
\newcommand{\specialcite}[1]{\@nameuse{b@#1}} %AKC

%%%% Ãƒâ€Ã‚Â°ÃƒÆ’Ã¢â‚¬Â¡Ãƒâ€Ã‚Â°NDEKÃƒâ€Ã‚Â°LER SAYFASINDAKÃƒâ€Ã‚Â° HÃƒâ€Ã‚Â°ZALAMALAR (INDENT MÃƒâ€Ã‚Â°KTARLARI)
\newcommand*\l@mistix{\@tocline{1}{0mm}{0mm}}
\renewcommand*\l@section{\@tocline{1}{1.1em}{1.5em}}
\renewcommand*\l@subsection{\@tocline{2}{2.1em}{2.5em}}
\renewcommand*\l@subsubsection{\@tocline{3}{3.3em}{3.0em}}
\newcommand*\l@subsubsubsection{\@tocline{4}{4.4em}{4.9em}}
\renewcommand*\l@table{\@tocline{1}{0em}{5.5em}}
\renewcommand*\l@figure\l@table

%\newcommand*\l@mistix{\@tocline{1}{0mm}{0mm}}
%\renewcommand*\l@section{\@tocline{1}{1.1em}{1.5em}}
%\renewcommand*\l@subsection{\@tocline{2}{1.9em}{2.3em}}
%\renewcommand*\l@subsubsection{\@toclinealper{3}{3.5em}{3.9em}}
%\renewcommand*\l@table{\@tocline{1}{0em}{5.5em}}
%\renewcommand*\l@figure\l@table


\newcommand*{\th@baslikbir}{
    \ClassError{inonutez}{*** You must specify the TITLE of your thesis! ***}
    {Use the \protect\title{} command in the preamble.}}

\newcommand*{\th@Titlebir}{
    \ClassError{inonutez}{*** You must specify the ENGLISH TITLE of your thesis! ***}
    {Use the \protect\title{}{}{} command in the preamble.}}

\newcommand*{\th@tarih}{
    \ClassError{inonutez}{*** You must specify the DATE of your thesis! ***}
    {Use the \protect\tarih{} command in the preamble.}}


\newcommand*{\th@TeziYoneten}{
    \ClassError{inonutez}{*** You must specify the TEZIYONETEN of your thesis! ***}
    {Use the \protect\TeziYoneten{} command in the preamble.}}

\newcommand*{\th@isimsoyisim}{
        \ClassError{inonutez}{*** You must specify the AUTHOR of your thesis! ***}
        {Use the \protect\author{}{} command in the \MessageBreak
                preamble. The first arg is your first name and \MessageBreak
                middle initial.  The second arg is your last name.}}
        
\newcommand{\th@abstractStash}{
    \ClassError{inonutez}{*** You must specify an abstract! ***}
    {Use the \protect\abstractpage[]{} command in the \MessageBreak
        preamble.  If your abstract runs over a page, \MessageBreak
        use the optional argument with the word 'long'.}
}

\newcommand{\th@AnahtarKelimeler}{}
\newcommand{\th@Keywords}{}

\newcommand{\th@ozetStash}{
    \ClassError{inonutez}{*** You must specify an ozet! ***}
    {Use the \protect\ozetpage[]{} command in the \MessageBreak
        preamble.  If your abstract runs over a page, \MessageBreak
        use the optional argument with the word 'long'.}
}

\newcommand{\th@AnaBilimDali}{
    \ClassError{inonutez}{*** You must specify an AnaBilimDali! ***}
    {Use the \protect\anabilimdali[]{} command in the \MessageBreak
        preamble.  If your abstract runs over a page, \MessageBreak
        use the optional argument with the word 'long'.}
}

\newcommand{\th@ozgecmisStash}{
    \ClassError{inonutez}{*** You must specify an ozgecmis ***}
    {Use the \protect\ozgecmispage[]{} command in the \MessageBreak
        preamble.  If your abstract runs over a page, \MessageBreak
        use the optional argument with the word 'long'.}
}

\newcommand{\summary}[1]{\th@StoreIn{\th@abstractStash}{#1}}
\newcommand{\ozet}[1]{\th@StoreIn{\th@ozetStash}{#1}}
\newcommand{\anahtarkelimeler}[1]{\th@StoreIn{\th@AnahtarKelimeler}{#1}}
\newcommand{\keywords}[1]{\th@StoreIn{\th@Keywords}{#1}}
\newcommand{\ozgecmis}[1]{\th@StoreIn{\th@ozgecmisStash}{#1}}
\newcommand{\tesekkur}[1]{\@TesekkurVartrue\th@StoreIn{\th@tesekkurStash}{#1}}
\newcommand{\onsoz}[1]{\tesekkur{#1}}
\newcommand{\sembollistesi}[1]{%
  \edef\th@tmp{\detokenize{#1}}%
  \ifx\th@tmp\@empty\else
    \@SembolListesiVartrue
    \th@StoreIn{\th@symbollistStash}{#1}%
  \fi
}
\newcommand{\kisaltmalistesi}[1]{%
  \edef\th@tmp{\detokenize{#1}}%
  \ifx\th@tmp\@empty\else
    \@KisaltmaListesiVartrue
    \th@StoreIn{\th@kisaltmalistStash}{#1}%
  \fi
}

\newcommand*{\th@AltBaslikGirinti}{\hspace*{1.25cm}}

\def\section{\@ifstar\unnumberedsection\numberedsection}
\def\numberedsection{\@ifnextchar[%]
  \numberedsectionwithtwoarguments\numberedsectionwithoneargument}
\def\unnumberedsection{\@ifnextchar[%]
  \unnumberedsectionwithtwoarguments\unnumberedsectionwithoneargument}
\def\numberedsectionwithoneargument#1{\numberedsectionwithtwoarguments[#1]{#1}}
\def\unnumberedsectionwithoneargument#1{\unnumberedsectionwithtwoarguments[#1]{#1}}
\def\numberedsectionwithtwoarguments[#1]#2{%
   \ifhmode\par\fi
  \removelastskip
  \vspace*{12pt}\goodbreak %ikinci derece baÃƒâ€¦Ã…Â¸lÃƒâ€Ã‚Â±k ÃƒÆ’Ã‚Â¼st boÃƒâ€¦Ã…Â¸luk
  \refstepcounter{section}%
  \noindent
  \th@AltBaslikGirinti
  \leavevmode
  \begingroup
  \th@HdFnt\th@ScSz
  \thesection\;\ 
  #2\quad
  \endgroup\goodbreak
  \addcontentsline{toc}{section}{\protect\numberline{\thesection}#1}}
\def\unnumberedsectionwithtwoarguments[#1]#2{%
  \ifhmode\par\fi
  \removelastskip
  \vspace*{8pt}\goodbreak %ikinci derece baÃƒâ€¦Ã…Â¸lÃƒâ€Ã‚Â±k alt boÃƒâ€¦Ã…Â¸luk
  \noindent
  \th@AltBaslikGirinti
  \leavevmode
  \begingroup
  \bfseries
  #2\quad
  \endgroup\goodbreak
  \addcontentsline{toc}{section}{#1}}
    
\def\subsection{\@ifstar\unnumberedsubsection\numberedsubsection}
\def\numberedsubsection{\@ifnextchar[%]
  \numberedsubsectionwithtwoarguments\numberedsubsectionwithoneargument}
\def\unnumberedsubsection{\@ifnextchar[%]
  \unnumberedsubsectionwithtwoarguments\unnumberedsubsectionwithoneargument}
\def\numberedsubsectionwithoneargument#1{\numberedsubsectionwithtwoarguments[#1]{#1}}
\def\unnumberedsubsectionwithoneargument#1{\unnumberedsubsectionwithtwoarguments[#1]{#1}}
\def\numberedsubsectionwithtwoarguments[#1]#2{%
  \ifhmode\par\fi
  \removelastskip
   \vspace*{8pt}\goodbreak %ÃƒÆ’Ã‚Â¼ÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â¼ncÃƒÆ’Ã‚Â¼ derece baÃƒâ€¦Ã…Â¸lÃƒâ€Ã‚Â±k ÃƒÆ’Ã‚Â¼st boÃƒâ€¦Ã…Â¸luk
  \refstepcounter{subsection}%
  \noindent
  \th@AltBaslikGirinti
  \leavevmode
  \begingroup
  \th@HdFnt\th@ScSz
  \thesubsection\;\ 
  #2\quad
  \endgroup\goodbreak
  \vspace*{4pt}\goodbreak %ÃƒÆ’Ã‚Â¼ÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â¼ncÃƒÆ’Ã‚Â¼ derece baÃƒâ€¦Ã…Â¸lÃƒâ€Ã‚Â±k alt boÃƒâ€¦Ã…Â¸luk
  \addcontentsline{toc}{subsection}{\protect\numberline{\thesubsection}#1}}
\def\unnumberedsubsectionwithtwoarguments[#1]#2{%
  \ifhmode\par\fi
  \removelastskip
  \vspace*{6pt}\goodbreak
  \noindent
  \th@AltBaslikGirinti
  \leavevmode
  \begingroup
  \bfseries
  #2\quad
  \endgroup\goodbreak
  \addcontentsline{toc}{subsection}{#1}}

\def\subsubsection{\@ifstar\unnumberedsubsubsection\numberedsubsubsection}
\def\subsubsubsection{\unnumberedsubsubsubsection}
\def\numberedsubsubsection{\@ifnextchar[%]
  \numberedsubsubsectionwithtwoarguments\numberedsubsubsectionwithoneargument}
\def\unnumberedsubsubsection{\@ifnextchar[%]
  \unnumberedsubsubsectionwithtwoarguments\unnumberedsubsubsectionwithoneargument}
\def\unnumberedsubsubsubsection{\@ifnextchar[%]
  \unnumberedsubsubsubsectionwithtwoarguments\unnumberedsubsubsubsectionwithoneargument}

\def\numberedsubsubsectionwithoneargument#1{\numberedsubsubsectionwithtwoarguments[#1]{#1}}
\def\unnumberedsubsubsectionwithoneargument#1{\unnumberedsubsubsectionwithtwoarguments[#1]{#1}}

\def\unnumberedsubsubsubsectionwithoneargument#1{\unnumberedsubsubsubsectionwithtwoarguments[#1]{#1}}

\def\numberedsubsubsectionwithtwoarguments[#1]#2{%
  \ifhmode\par\fi
  \removelastskip
   \vspace*{8pt}\goodbreak % dorduncu derece ve sonrasi numarasiz yardimci basliktir.
  \noindent
  \th@AltBaslikGirinti
  \leavevmode
  \begingroup
  \th@HdFnt\th@ScSz
  #2\quad
  \endgroup\goodbreak
  \vspace*{4pt}\goodbreak}
\def\unnumberedsubsubsectionwithtwoarguments[#1]#2{%
  \ifhmode\par\fi
  \removelastskip
  \vspace*{6pt}\goodbreak
  \noindent
  \th@AltBaslikGirinti
  \leavevmode
  \begingroup
  \bfseries
  #2\quad
  \endgroup\goodbreak}

\def\unnumberedsubsubsubsectionwithtwoarguments[#1]#2{%
  \ifhmode\par\fi
  \removelastskip
  \vspace*{6pt}\goodbreak
  \noindent
  \th@AltBaslikGirinti
  \leavevmode
  \begingroup
  \bfseries
  #2\quad
  \endgroup\goodbreak}
 
\def\@part[#1]#2{\ifnum \c@secnumdepth >\m@ne
                 \refstepcounter{part}%
                 \addcontentsline{toc}{part}{\thepart\protect\hspace{1em}#1}%
                 \addcontentsline{toc}{part}{#1}%
    \else
       \relax  
    \fi
    \markboth{}{}%
    {\centering
     \interlinepenalty \@M
     \normalfont
     \ifnum \c@secnumdepth >-2\relax
       \huge\bfseries \partname\nobreakspace\thepart
       \par
       \vskip 20\p@
     \fi
     \Huge \bfseries #2\par}%
    \@endpart}

\newif\if@appendix\@appendixfalse

\renewcommand\chapter{  
                      \global\@topnum\z@
                      \@afterindentfalse
                      \secdef\@chapter\@schapter}

%%EK BÃƒÆ’Ã¢â‚¬â€œLÃƒÆ’Ã…â€œMÃƒÆ’Ã…â€œNDE BÃƒÆ’Ã¢â‚¬â€œLÃƒÆ’Ã…â€œM NUMARASI OLMASIN DÃƒâ€Ã‚Â°YE
\newcommand{\eklerkapak}{\global\@topnum\z@
                      \@afterindentfalse
                      \secdef\@eklerkapak\@schapter}

\def\@chapter[#1]#2{\BolumSagdaKalsinNolu
                    \ifnum \c@secnumdepth >\m@ne
                         \refstepcounter{chapter}%
                          \addtocontents{toc}{\protect\addvspace{-10\p@}}
                          %\addtocontents{toc}{\protect\addvspace{0\p@}}%
                          \if@appendix
	                      \addtocontents{toc}{\protect\addvspace{0\p@}}
                              \addcontentsline{toc}{section}{\protect #1}										
% \relax
								  \else
                              \addcontentsline{toc}{chapter}{\thechapter. \protect \bf{#1}}
								  \fi
                    \else
                      \relax
                    \fi
                    \chaptermark{#1}%
                    %LoT ve LoF da bÃƒÆ’Ã‚Â¶lÃƒÆ’Ã‚Â¼mler arasÃƒâ€Ã‚Â± geÃƒÆ’Ã‚Â§iÃƒâ€¦Ã…Â¸de bir boÃƒâ€¦Ã…Â¸luk bÃƒâ€Ã‚Â±rakÃƒâ€Ã‚Â±lacaksa...
                    %\addtocontents{lof}{\protect\addvspace{10\p@}}%
                    %\addtocontents{lot}{\protect\addvspace{10\p@}}%
                    \if@twocolumn
                      \@topnewpage[\@makechapterhead{#2}]%
                    \else
                      \@makechapterhead{#2}%
                      \@afterheading
                    \fi
                    }

%%EK BÃƒÆ’Ã¢â‚¬â€œLÃƒÆ’Ã…â€œMÃƒÆ’Ã…â€œNDE BÃƒÆ’Ã¢â‚¬â€œLÃƒÆ’Ã…â€œM NUMARASI OLMASIN DÃƒâ€Ã‚Â°YE
\def\@eklerkapak[#1]#2{\BolumSagdaKalsinNolu
                    \ifnum \c@secnumdepth >\m@ne
                         \refstepcounter{chapter}%
                          \addtocontents{toc}{\protect\addvspace{-10\p@}}
                          %\addtocontents{toc}{\protect\addvspace{0\p@}}%
                          \if@appendix
										\relax
								  \else
										\addcontentsline{toc}{chapter}{\protect \bf{\EklerinBasligi}}
								  \fi
                    \else
                      \relax
                    \fi
                    \chaptermark{\EklerinBasligi}%
                    %LoT ve LoF da bÃƒÆ’Ã‚Â¶lÃƒÆ’Ã‚Â¼mler arasÃƒâ€Ã‚Â± geÃƒÆ’Ã‚Â§iÃƒâ€¦Ã…Â¸de bir boÃƒâ€¦Ã…Â¸luk bÃƒâ€Ã‚Â±rakÃƒâ€Ã‚Â±lacaksa...
                    %\addtocontents{lof}{\protect\addvspace{10\p@}}%
                    %\addtocontents{lot}{\protect\addvspace{10\p@}}%
                   \if@twocolumn
                     \@topnewpage[\@makechapterheadEK{\EklerinBasligi}]%
                   \else
                     \@makechapterheadEK{\EklerinBasligi}%
                     \@afterheading
                   \fi
}

\def\@makechapterhead#1{
    \vspace*{\ChapterUstenBosluk}%
%		\addcontentsline{toc}{section}{\protect #1}
    {\parindent \z@
    \normalfont
    \ifnum \c@secnumdepth >\m@ne
     \if@appendix 
%      \th@HdFnt\th@ScSz \if@Ingilizce APPENDIX \else EK \fi \thechapter\;: #1
       \noindent\th@HdFnt\th@ScSz #1\par\nobreak
%        \unnumberedsectionwithoneargument{#1}
%       \addcontentsline{toc}{subsection}{#1}
     \else
       \centering
           \th@HdFnt\th@ChSz \thechapter. \;#1 
        \par\nobreak
        \vskip 12\p@ %birinci derece baÃƒâ€¦Ã…Â¸lÃƒâ€Ã‚Â±k alt boÃƒâ€¦Ã…Â¸luk
    \fi\fi
    \interlinepenalty\@M
    \th@HdFnt\th@ChSz \par\nobreak
    %\vskip 20\p@
  }}

%%EK BÃƒÆ’Ã¢â‚¬â€œLÃƒÆ’Ã…â€œMÃƒÆ’Ã…â€œNDE BÃƒÆ’Ã¢â‚¬â€œLÃƒÆ’Ã…â€œM NUMARASI OLMASIN DÃƒâ€Ã‚Â°YE
\def\@makechapterheadEK#1{
    \vspace*{\ChapterUstenBosluk}%
    {\parindent \z@ \centering
    \normalfont
    \ifnum \c@secnumdepth >\m@ne
         \th@HdFnt\th@ChSz #1
     \fi
    \interlinepenalty\@M
    \th@HdFnt\th@ChSz \par\nobreak
    %\vskip 20\p@
  }}


\def\@schapter#1{\BolumSagdaKalsinNolu
    \@makeschapterhead{#1}
    \@afterheading
    }

\def\@makeschapterhead#1{
    \vspace*{\ChapterUstenBosluk}%
    {\parindent \z@ \centering
    \normalfont
    \interlinepenalty\@M
    \th@HdFnt\th@ChSz #1\par\nobreak
    \vskip 12\p@
  }}


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  
\newcommand*{\th@DisKapak}{
      \BolumSagdaKalsin
      \thispagestyle{empty}
      \begin{list}{}{\setlength{\leftmargin}{0cm}\setlength{\rightmargin}{-2cm}}
        \vspace*{-8.5mm}
        \centering\item[]
    \begin{textblock}{}[0,1](2.23,2.41)
          \if@Ingilizce 
           \hspace*{\kaydirmaboyuENG}
      \else
           \hspace*{\kaydirmaboyuTR}
          \fi
          \underline{{\bf\th@EnstituUpper}}\\
      \hspace*{130pt} %FBE ingilizce yeni baslik icin
          \underline{\MakeUppercase{\bf\th@Instituteiki}}\\ %FBE ingilizce yeni baslik icin
    \end{textblock}
        \vspace*{55mm}
    \hspace{-20mm}
        \begin{tabular}{c}
         \th@titleFtSz\Baslikspacing \Baslikbir \\
         \th@titleFtSz\Baslikspacing \Baslikiki \\
         \th@titleFtSz\Baslikspacing \Baslikuc \\
        \end{tabular}\\
        \vspace*{55mm}
    \hspace{-20mm}
        \begin{tabular}[b]{c}
         \th@titleFtSz \TezSeviyesi  \\
                 \\
         \th@titleFtSz \th@isimsoyisim  \\
           \\
        \end{tabular}\\
        \vspace*{27mm}
    \hspace{-20mm}
        \begin{tabular}[t]{c}
        {\th@titleAnaBilimDaliFtSz \Anabilim}\\
        \\
        {\th@titleAnaBilimDaliFtSz \Program}
        \end{tabular}\\
        \vspace*{14mm}
    \hspace{-20mm}
        {\if@Bez
        \begin{tabular}{c}
         \\
        \end{tabular}\\
         \else 
        \begin{tabular}{c}
         \th@titleFtSz\DanismanBaslik : \th@titleFtSz \th@TezYoneticisi\\
        \end{tabular}\\
        \fi}
        \vspace*{22mm}
    \hspace{-20mm}
        \begin{tabular}{c}
         \th@titleFtSz \TarihBuyuk \\
        \end{tabular}
    \end{list}
}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\newcommand*{\th@IcKapak}{
      \BolumSagdaKalsin
      \thispagestyle{empty}
      \begin{list}{}{\setlength{\leftmargin}{0cm}\setlength{\rightmargin}{-2cm}}
        \vspace*{-8.5mm}
        \centering\item[]
    \begin{textblock}{}[0,1](2.23,2.41)
          \if@Ingilizce 
           \hspace*{\kaydirmaboyuENG}
      \else
           \hspace*{\kaydirmaboyuTR}
          \fi  
          \underline{{\bf\th@EnstituUpper}}\\
      \hspace*{130pt} %FBE ingilizce yeni baslik icin
          \underline{\MakeUppercase{\bf\th@Instituteiki}}\\ %FBE ingilizce yeni baslik icin
    \end{textblock}
        \vspace*{55mm}
    \hspace{-20mm}
        \begin{tabular}{c}
         \th@titleFtSz\Baslikspacing \Baslikbir \\
         \th@titleFtSz\Baslikspacing \Baslikiki \\
         \th@titleFtSz\Baslikspacing \Baslikuc \\
        \end{tabular}\\
        \vspace*{55mm}
    \hspace{-20mm}
        \begin{tabular}[b]{c}
         \th@titleFtSz \TezSeviyesi  \\
                 \\
         \th@titleFtSz \th@isimsoyisim  \\
         \th@titleFtSz (\th@ogrencino)\\
        \end{tabular}\\
        \vspace*{22mm}
    \hspace{-20mm}
        \begin{tabular}[t]{c}
        {\th@titleAnaBilimDaliFtSz \Anabilim}\\
        \\
        {\th@titleAnaBilimDaliFtSz \Program}
        \end{tabular}\\
        \vspace*{14mm}
    \hspace{-20mm}
        \begin{tabular}{c}
         \th@titleFtSz\DanismanBaslik : \th@titleFtSz \th@TezYoneticisi\\
         \ifthenelse{\equal{\th@esdanisman}{}}{}{ \bf{Eş Danışman:} \bf{\th@esdanisman} \\}
        \end{tabular}\\
        \vspace*{17mm}
	\hspace{-20mm}
        \begin{tabular}{c}
         \th@titleFtSz \TarihBuyuk \\
        \end{tabular}
    \end{list}
}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
\newcommand*{\th@IcKapakTurkce}{
      \BolumSagdaKalsin
      \thispagestyle{empty}
      \begin{list}{}{\setlength{\leftmargin}{0cm}\setlength{\rightmargin}{-2cm}}
        \vspace*{-8.5mm}
        \centering\item[]
    \begin{textblock}{}[0,1](1.85,2)
           \hspace*{\kaydirmaboyuTR}
          \underline{{\bf\th@EnstituUpperTR}}\\
    \end{textblock}
        \vspace*{55mm}
    \hspace{-20mm}
        \begin{tabular}{c}
         \th@titleFtSz\Baslikspacing \th@baslikbir \\
         \th@titleFtSz\Baslikspacing \th@baslikiki \\
         \th@titleFtSz\Baslikspacing \th@baslikuc \\
        \end{tabular}\\
        \vspace*{55mm}
    \hspace{-20mm}
        \begin{tabular}[b]{c}
         \th@titleFtSz \TezSeviyesiTR  \\
                 \\
         \th@titleFtSz \th@isimsoyisim  \\
         \th@titleFtSz (\th@ogrencino)\\
        \end{tabular}\\
        \vspace*{27mm}
    \hspace{-20mm}
        \begin{tabular}[t]{c}
        {\th@titleAnaBilimDaliFtSz \th@AnaBilimDali}\\
        \\
        {\th@titleAnaBilimDaliFtSz \th@Programi}
        \end{tabular}\\
        \vspace*{14mm}
    \hspace{-20mm}
        \begin{tabular}{c}
         \th@titleFtSz\DanismanBaslik : \th@titleFtSz \th@TezYoneticisi\\
         \ifthenelse{\equal{\th@esdanisman}{}}{}{\th@titleFtSz\EsDanismanBaslik : \th@titleFtSz \th@esdanisman\\}
        \end{tabular}\\
        \vspace*{20mm}
    \hspace{-20mm}
        \begin{tabular}{c}
         \th@titleFtSz \th@tarih \\
        \end{tabular}
    \end{list}
}

\newcommand*{\th@IcKapakIngilizce}{
      \BolumSagdaKalsin
      \thispagestyle{empty}
      \begin{list}{}{\setlength{\leftmargin}{0cm}\setlength{\rightmargin}{-2cm}}
        \vspace*{-8.5mm}
        \centering\item[]
    \begin{textblock}{}[0,1](1.85,2)
           \hspace*{\kaydirmaboyuENG}
          \underline{{\bf\th@EnstituUpperENG}}\\
    \end{textblock}
        \vspace*{55mm}
    \hspace{-20mm}
        \begin{tabular}{c}
         \th@titleFtSz\Baslikspacing \th@Titlebir \\
         \th@titleFtSz\Baslikspacing \th@Titleiki \\
         \th@titleFtSz\Baslikspacing \th@Titleuc \\
        \end{tabular}\\
        \vspace*{55mm}
    \hspace{-20mm}
        \begin{tabular}[b]{c}
         \th@titleFtSz \TezSeviyesiENG  \\
                 \\
         \th@titleFtSz \th@isimsoyisim  \\
         \th@titleFtSz (\th@ogrencino)\\
        \end{tabular}\\
        \vspace*{27mm}
    \hspace{-20mm}
        \begin{tabular}[t]{c}
        {\th@titleAnaBilimDaliFtSz \th@Department}\\
        \\
        {\th@titleAnaBilimDaliFtSz \th@Programme}
        \end{tabular}\\
        \vspace*{14mm}
    \hspace{-20mm}
        \begin{tabular}{c}
         \th@titleFtSz {Thesis Advisor}: \th@titleFtSz \th@TezYoneticisiENG\\
         \ifthenelse{\equal{\th@esdanismanENG}{}}{}{ \bf{Co-Advisor:} \bf{\th@esdanismanENG} \\}
        \end{tabular}\\
        \vspace*{22mm}
    \hspace{-20mm}
        \begin{tabular}{c}
         \th@titleFtSz \th@date \\
        \end{tabular}
    \end{list}
}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
\newcommand*{\th@kapakBaslikFt}{\bfseries\fontsize{32}{36.8}\selectfont}
\newcommand*{\th@kapakTezFt}{\bfseries\fontsize{26}{30}\selectfont}
\newcommand*{\th@kapakAdFt}{\bfseries\fontsize{21}{24}\selectfont}
\newcommand*{\th@kapakAltFt}{\bfseries\fontsize{15}{18}\selectfont}
\newcommand*{\th@disKapakLogoFt}{\bfseries\fontsize{8.5}{10.2}\selectfont}
\newcommand*{\th@disKapakBaslikFt}{\sffamily\bfseries\fontsize{32}{36.8}\selectfont}
\newcommand*{\th@disKapakTezFt}{\sffamily\bfseries\fontsize{26}{30}\selectfont}
\newcommand*{\th@disKapakEngFt}{\sffamily\bfseries\fontsize{15}{18}\selectfont}
\newcommand*{\th@disKapakAdFt}{\sffamily\bfseries\fontsize{21}{24}\selectfont}
\newcommand*{\th@icKapakBaslikFt}{\sffamily\bfseries\fontsize{11}{16.5}\selectfont}
\newcommand*{\th@icKapakFt}{\sffamily\fontsize{11}{16.5}\selectfont}
\newcommand*{\th@kapakSeritFt}{\sffamily\bfseries\fontsize{15}{18}\selectfont}
\newcommand*{\th@KapakSeritRenk}{%
  \if@Doktora
    \color[rgb]{0.96,0.69,0.00}%
  \else
    \color[rgb]{0.00,0.45,0.52}%
  \fi
}



\renewcommand*{\th@DisKapak}{
    \thispagestyle{empty}
    \enlargethispage{25mm}
    \vspace*{-2mm}
    \begin{center}
      \IfFileExists{assets/iu-fbe-amblem.png}
        {\includegraphics[width=26mm]{assets/iu-fbe-amblem.png}\par\vspace*{2mm}}
        {\IfFileExists{assets/inonu-logo.png}{\includegraphics[width=26mm]{assets/inonu-logo.png}\par\vspace*{2mm}}{}}
      {\th@icKapakFt\bfseries T.C.\par}
      {\th@icKapakFt\bfseries İNÖNÜ ÜNİVERSİTESİ\par}
      {\th@icKapakFt\bfseries FEN BİLİMLERİ ENSTİTÜSÜ\par}
      \vspace*{24mm}
      {\th@disKapakBaslikFt\setlength{\baselineskip}{36.8pt}%
        \th@TrUpper{\Baslikbir}\par
        \ifthenelse{\equal{\Baslikiki}{}}{}{\th@TrUpper{\Baslikiki}\par}%
        \ifthenelse{\equal{\Baslikuc}{}}{}{\th@TrUpper{\Baslikuc}\par}%
      }
      \vspace*{14mm}
      {\th@disKapakAdFt \th@TrUpper{\th@isimsoyisim}\par}
      \vspace*{18mm}
      {\th@kapakAltFt \th@TrUpper{\Anabilim}\par}
      \ifthenelse{\equal{\Program}{}}{}{{\vspace*{2mm}\th@kapakAltFt \th@TrUpper{\Program}\ \if@Ingilizce PROGRAMME\else PROGRAMI\fi\par}}
      \vspace*{18mm}
      {\th@disKapakTezFt \th@TrUpper{\TezSeviyesi}\par}
      \vspace*{2mm}
      {\th@disKapakEngFt \th@TrUpper{\TezSeviyesiENG}\par}
    \end{center}
    \th@DrawDisKapakSerit{\th@TrUpper{\th@kapaksehri, \th@kapakyili}}
    \clearpage
}

\newcommand*{\th@SirtKapak}{
    \ifnum\value{page}>1\clearpage\fi
    \thispagestyle{empty}
    \enlargethispage{25mm}
    \sffamily
    \begin{textblock*}{\paperwidth}(0mm,125mm)
      \centering
      \rotatebox{90}{%
        \begin{minipage}{105mm}
          \centering
          {\bfseries\fontsize{12}{14}\selectfont
          \MakeUppercase{\th@isimsoyisim}\hspace{4mm}|\hspace{4mm}%
          \MakeUppercase{\Baslikbir}%
          \ifthenelse{\equal{\Baslikiki}{}}{}{ \MakeUppercase{\Baslikiki}}%
          \ifthenelse{\equal{\Baslikuc}{}}{}{ \MakeUppercase{\Baslikuc}}\par}
        \end{minipage}%
      }
    \end{textblock*}
    \vspace*{\fill}
    \th@DrawKapakSerit{\th@kapakyili}
    \clearpage
}

\newcommand*{\sirtkapak}{\th@SirtKapak}



\renewcommand*{\th@IcKapak}{
    \clearpage
    \thispagestyle{empty}
    \vspace*{-7mm}
    \begin{center}
      {\th@icKapakFt\bfseries T.C.\par}
      {\th@icKapakFt\bfseries İNÖNÜ ÜNİVERSİTESİ\par}
      {\th@icKapakFt\bfseries FEN BİLİMLERİ ENSTİTÜSÜ\par}
      \vspace*{23mm}
      {\th@icKapakBaslikFt
      \th@TrUpper{\Baslikbir}\par
      \ifthenelse{\equal{\Baslikiki}{}}{}{\th@TrUpper{\Baslikiki}\par}
      \ifthenelse{\equal{\Baslikuc}{}}{}{\th@TrUpper{\Baslikuc}\par}}
      \vspace*{20mm}
      {\th@icKapakFt\bfseries \th@isimsoyisim\par}
      \vspace*{24mm}
      {\th@icKapakFt\bfseries \Anabilim\par}
      \th@MaybeProgramLine
      \vspace*{11mm}
      {\th@icKapakFt\bfseries \TezSeviyesi\par}
      \vspace*{25mm}
      {\th@icKapakFt\bfseries \DanismanBaslik\par}
      {\th@icKapakFt\bfseries \th@TezYoneticisi\par}
      \ifthenelse{\equal{\th@esdanisman}{}}{}{%
        \vspace*{5mm}
        {\th@icKapakFt\bfseries \EsDanismanBaslik{} (Varsa)\par}
        {\th@icKapakFt\bfseries \th@esdanisman\par}}
      \ifthenelse{\equal{\th@bapdestegi}{}}{}{%
        \vfill
        {\parbox{0.92\textwidth}{\centering\th@icKapakFt
        Bu Araştırma İnönü Üniversitesi Bilimsel Araştırma Projeleri Birimi Tarafından\par
        \th@bapdestegi{} Proje Numarası ile Desteklenmiştir.\par}}}
      \vfill
      {\th@icKapakFt\bfseries\underline{\th@kapaksehri}\par}
      {\th@icKapakFt\bfseries \th@kapakyili\par}
    \end{center}
    \clearpage
}

\newcommand*{\th@IthafSayfasi}{
      \BolumSagdaKalsinNolu
      \thispagestyle{empty}
    \vspace*{0.4\textheight}
        \begin{flushright}
     \textbf{\emph{\th@Ithaf}}
        \end{flushright}
}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
\newcommand*{\th@ImzaCizgisi}{\rule{32mm}{0.4pt}}

\newcommand{\th@onaypage}{
    \BolumSagdaKalsin
    \hyphenpenalty=100
    \singlespacing
\vspace*{18mm}
\if@Ingilizce
\begin{center}
{\th@ChapterStyle APPROVAL}
\end{center}
\vspace*{8mm}
{\th@isimsoyisim}, a \if@Doktora Ph.D.\ \else M.Sc.\ \fi student of
Inonu University \th@Institute\ student ID \th@ogrencino\ successfully defended the thesis
entitled ``\Baslikbir\ifthenelse{\equal{\Baslikiki}{}}{}{ \Baslikiki}\ifthenelse{\equal{\Baslikuc}{}}{}{ \Baslikuc}'',
which he/she prepared after fulfilling the
requirements specified in the associated legislations,
before the jury whose signatures are below.

\vspace*{14mm}
\noindent\begin{tabular*}{\textwidth}{@{}p{35mm}p{72mm}@{\extracolsep{\fill}}p{35mm}@{}}
   &  &  \\
   &  &  \\
   &  &  \\
  \bf{Thesis Advisor :}& \bf{\th@TezYoneticisi} & 
\th@ImzaCizgisi \\
   & \th@TezYoneticisiUniv  &  \\
\ifthenelse{\equal{\th@esdanisman}{}}{}{   &  &  \\
   &  &  \\
  \bf{Co-advisor :}& \bf{\th@esdanisman} & 
\th@ImzaCizgisi \\
   & \th@esdanismanuniv  &  \\}
   &  &  \\
   &  &  \\
  \bf{Jury Members :}& \bf{\th@juribir} & 
\th@ImzaCizgisi \\
   & \th@juribiruniv  &  \\
   &  &  \\
   &  &  \\
                        & \bf{\th@juriiki} & 
\th@ImzaCizgisi \\
   & \th@juriikiuniv  &  \\
   &  &  \\
   &  &  \\
                        & \bf{\th@juriuc} & 
\th@ImzaCizgisi \\
   & \th@juriucuniv  &  \\
   &  &  \\
   &  &  \\
\ifthenelse{\equal{\th@juridort}{}}{}{ & 
\bf{\th@juridort} & 
\th@ImzaCizgisi \\
   & \th@juridortuniv  &  \\}
   &  &  \\
   &  &  \\
\ifthenelse{\equal{\th@juribes}{}}{}{ & \bf{\th@juribes} & 
\th@ImzaCizgisi \\
   & \th@juribesuniv  &  \\}
   &  &  \\
   &  &  \\
\end{tabular*}

\noindent\begin{tabular}{@{}l l@{}}
   \bf{Date of Submission :} & \bf{\th@submissiondate}  \\
   \bf{Date of Defense :} & \bf{\th@defencedate}  \\
\end{tabular}
\else
\begin{center}
{\th@ChapterStyle KABUL VE ONAY}
\end{center}
\vspace*{8mm}
İnönü Üniversitesi, \th@Enstitu'nün \th@ogrencino\ numaralı \if@Doktora Doktora
\else Yüksek Lisans \fi\ Öğrencisi 
{\th@isimsoyisim}, ilgili 
yönetmeliklerin belirlediği gerekli tüm şartları yerine getirdikten
sonra hazırladığı 
``\Baslikbir\ifthenelse{\equal{\Baslikiki}{}}{}{ \Baslikiki}\ifthenelse{\equal{\Baslikuc}{}}{}{ \Baslikuc}''
baş\-lı k\-lı
tezini aşağı da imzaları olan jüri önünde
başarı ile sunmuştur.

\vspace*{14mm}
\noindent\begin{tabular*}{\textwidth}{@{}p{35mm}p{72mm}@{\extracolsep{\fill}}p{35mm}@{}}
   &  &  \\
   &  &  \\
   &  &  \\
  \bf{Tez Danışmanı:}& \bf{\th@TezYoneticisi} &
\th@ImzaCizgisi \\
   & \th@TezYoneticisiUniv  &  \\
\ifthenelse{\equal{\th@esdanisman}{}}{}{   &  &  \\
   &  &  \\
  \bf{Eş Danışman:}& \bf{\th@esdanisman} &
\th@ImzaCizgisi \\
   & \th@esdanismanuniv  &  \\}
   &  &  \\
   &  &  \\
  \bf{Jüri Üyeleri :}& \bf{\th@juribir} & 
\th@ImzaCizgisi \\
   & \th@juribiruniv  &  \\
   &  &  \\
   &  &  \\
                        & \bf{\th@juriiki} & 
\th@ImzaCizgisi \\
   & \th@juriikiuniv  &  \\
   &  &  \\
   &  &  \\
                        & \bf{\th@juriuc} & 
\th@ImzaCizgisi \\
   & \th@juriucuniv  &  \\
   &  &  \\
   &  &  \\
\ifthenelse{\equal{\th@juridort}{}}{}{ & 
\bf{\th@juridort} & 
\th@ImzaCizgisi \\
   & \th@juridortuniv  &  \\}
   &  &  \\
   &  &  \\
\ifthenelse{\equal{\th@juribes}{}}{}{ & \bf{\th@juribes} 
& 
\th@ImzaCizgisi \\
   & \th@juribesuniv  &  \\}
   &  &  \\
   &  &  \\
\end{tabular*}

\noindent\begin{tabular}{@{}l l@{}}
   \bf{Teslim Tarihi :} & \bf{\th@tezvermetarih}  \\
   \bf{Savunma Tarihi :} & \bf{\th@tezsavunmatarih}  \\
\end{tabular}
\vspace*{10mm}

\noindent Bu tez, jüri üyeleri tarafından \textbf{\th@oy} ile kabul edilmiş
ve Enstitü Yönetim Kurulu'nun \textbf{\th@yonetimkurulutarih} tarihli,
\textbf{\th@yonetimkurulukararno} sayılı kararı ile onaylanmıştır.

\vspace*{10mm}

\begin{center}
\ifthenelse{\equal{\th@EnstituMuduru}{}}{}{\bf{\th@EnstituMuduru}\\ Enstitü Müdürü}
\end{center}
\fi
    \sloppy
   }
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 

\newcommand{\th@EtikBeyanSayfasi}{
     \BolumSagdaKalsinNolu
     \thispagestyle{empty}
     \sffamily\fontsize{11}{16.5}\selectfont
     \oneandonehalf
     \hyphenpenalty=5000
     \vspace*{-6mm}
     \begin{center}
       {\bfseries T.C.\\ İNÖNÜ ÜNİVERSİTESİ\\ FEN BİLİMLERİ ENSTİTÜSÜ MÜDÜRLÜĞÜNE}

       \vspace*{5mm}
       {\bfseries ETİK VE YAPAY ZEK\^A KULLANIM BEYANI}
     \end{center}
     \vspace*{4mm}
     \noindent \makebox[45mm]{\dotfill}/\makebox[45mm]{\dotfill}/20\makebox[20mm]{\dotfill}\par

     \vspace*{4mm}
     \noindent İnönü Üniversitesi Lisansüstü Tez Yazım Kurallarına uygun olarak,
     ``\th@TezYoneticisi'' danışmanlığında hazırlayıp sunduğum
     ``\th@FullTitle'' başlıklı \if@Doktora doktora\else yüksek lisans\fi{} tezinde;

     \vspace*{3mm}
     \noindent\textbf{1. ETİK VE BİLİMSEL SORUMLULUKLARIM:}
     \begin{itemize}\setlength\itemsep{0pt}
       \item Tezimde yer alan verileri, bilgileri ve belgeleri akademik ve etik kurallar çerçevesinde elde ettiğimi, değerlendirdiğimi ve sonuçları bilimsel etik ve ahlak kurallarına uygun olarak sunduğumu,
       \item Çalışmada yararlandığım tüm kaynaklara bilimsel kurallara uygun şekilde atıfta bulunduğumu ve kaynak gösteriminde APA 7. baskı kurallarına uyduğumu,
       \item Tezimin özgün olduğunu, çalışma ve yazım sürecinde patent ve telif haklarını ihlal edici hiçbir davranışta bulunmadığımı,
       \item Aksi bir durumda doğabilecek tüm hukuki ve akademik sonuçları kabul ettiğimi,
     \end{itemize}
     \noindent\textbf{2. YAPAY ZEK\^A KULLANIMINA İLİŞKİN BEYANIM:}

     \noindent (\IfStrEq{\th@yapayzekakullanimi}{hayir}{X}{ }) Tez yazım sürecinde yapay zek\^a tabanlı araçlardan faydalanmadım.\\
     (\IfStrEq{\th@yapayzekakullanimi}{evet}{X}{ }) Tez yazım sürecinde yapay zek\^a tabanlı araçlardan faydalandım.
     \begin{itemize}\setlength\itemsep{0pt}
       \item Yapay zek\^a araçlarını yalnızca bilimsel üretim sürecini desteklemek amacıyla kullandığımı,
       \item Kullanımın hipotez geliştirme, teorik tartışma ve yorumlama gibi üst düzey akademik becerileri içermediğini,
       \item Kullanımın tezin özgünlüğüne, bilimsel etik kurallarına ve ilgili mevzuata aykırı olmadığını,
       \item Usulsüz kullanımlara kesinlikle başvurmadığımı,
       \item Kullanılan yapay zek\^a araçlarının ve işlevlerinin, danışmanımın bilgisi dâhilinde, ekte verilen tabloda şeffaf biçimde belirtildiğini,
       \item Yükseköğretim Kurulu Bilimsel Araştırma ve Yayın Faaliyetlerinde Üretken Yapay Zek\^a Kullanımına Dair Etik Rehber'de belirtilen ilkelere riayet ettiğimi
     \end{itemize}
     \noindent kabul ve taahhüt ederim.

     \vspace*{8mm}
     \noindent Öğrencinin Adı Soyadı: \th@isimsoyisim\par
     \noindent İmza: \dotfill

     \IfStrEq{\th@yapayzekakullanimi}{evet}{%
       \vspace*{5mm}
       \noindent\textbf{EK: Yapay Zek\^a Kullanım Tablosu}\par
       \th@yapayzekatablosu
     }{}
}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
\newcommand{\th@Onsoz}{
     \BolumSagdaKalsinNolu
     \thispagestyle{empty}
     \Ozetspacing
     \hyphenpenalty=5000
     \vspace*{\UstenBosluk}
     \begin{list}{}{\setlength{\leftmargin}{0cm}\setlength{\rightmargin}{0cm}}
     \item[]
     \th@ChapterStyle\prefacename\\
     \end{list}
    \vspace*{-5mm}
    \sloppy
    \th@tesekkurStash   % the actual tesekkur
    \vspace{30pt} \\
    \TarihKucuk \hfill \th@isimsoyisim
    
    \vspace*{-2.54mm} \hfill \th@Unvan\\
    
    % 2025 kilavuzuna gore tesekkur/onsoz sayfasi icindekilere alinmaz.
}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\newcommand{\th@ozetpage}{
     \BolumSagdaKalsinNolu
     \addtocontents{toc}{\protect\addvspace{-12\p@}} %AKC
     \addcontentsline{toc}{chapter}{\bf{\protect\ozetnameToC}} %AKC
     \vspace*{\UstenBosluk}
       \begin{center}
        \begin{tabular}{c}
         {\sffamily\bfseries\fontsize{14}{16.8}\selectfont ÖZET} \\
                  \\
         \th@titleFtSz\Baslikspacing \th@baslikbir \\
         \th@titleFtSz\Baslikspacing \th@baslikiki \\
         \th@titleFtSz\Baslikspacing \th@baslikuc \\
                  \\
        \end{tabular}
       \end{center}
%     \begin{list}{}{\setlength{\leftmargin}{0cm}\setlength{\rightmargin}{0cm}}
%     \item[]
%     \th@ChapterStyle \th@baslikbir\ \th@baslikiki\ \th@baslikuc  \\
%     \vspace*{10pt}\\
%     \th@ChapterStyle \abstractname\ \\
%     \end{list}
     \Ozetspacing
     \vspace*{-5mm}
     \sloppy
     \th@ozetStash   % the actual ozet
     \par\vspace{6pt}\noindent\textbf{Anahtar Kelimeler:} \th@AnahtarKelimeler
     }
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%    
\newcommand{\th@Summarypage}{
     \BolumSagdaKalsinNolu
     \addtocontents{toc}{\protect\addvspace{-10\p@}} %AKC
     \addcontentsline{toc}{chapter}{\bf{\protect\abstractnameToC}} %AKC
     \vspace*{\UstenBosluk}
       \begin{center}
        \begin{tabular}{c}
         {\sffamily\bfseries\fontsize{14}{16.8}\selectfont ABSTRACT} \\
                  \\
         \th@titleFtSz\Baslikspacing \th@Titlebir \\
         \th@titleFtSz\Baslikspacing \th@Titleiki \\
         \th@titleFtSz\Baslikspacing \th@Titleuc \\
                  \\
        \end{tabular}
       \end{center}
     \singlespacing
     \vspace*{-5mm}
     \sloppy
     \th@abstractStash   % the actual abstract
     \par\vspace{6pt}\noindent\textbf{Keywords:} \th@Keywords
     }
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%\newcommand{\th@ozgecmispage}{
%     \BolumSagdaKalsinNolu
%     \vspace*{\UstenBosluk}
%     \begin{list}{}{\setlength{\leftmargin}{0cm}\setlength{\rightmargin}{0cm}}
%     \item[]
%     \th@ChapterStyle\ozgecmisname\\
%     \end{list}
%	  \singlespacing
%     \vspace*{-2mm}
%     \sloppy
%     \th@ozgecmisStash   % the actual ozgecmis
%          \addtocontents{toc}{\protect\addvspace{-10\p@}}
%    \addcontentsline{toc}{chapter}{\bf{\protect\ozgecmisnameToC}}%
%}


\newcommand{\th@ozgecmispage}{
    \clearpage % Yeni bir sayfa baÃƒâ€¦Ã…Â¸lat
    \setcounter{page}{\value{page}} % Sayfa numarasÃƒâ€Ã‚Â±nÃƒâ€Ã‚Â± ÃƒÆ’Ã‚Â¶nceki sayfaya devam ettir
    \phantomsection % BaÃƒâ€¦Ã…Â¸lÃƒâ€Ã‚Â±k sayfasÃƒâ€Ã‚Â± iÃƒÆ’Ã‚Â§in doÃƒâ€Ã…Â¸ru sayfa numarasÃƒâ€Ã‚Â±nÃƒâ€Ã‚Â± almak
    \BolumSagdaKalsinNolu % BaÃƒâ€¦Ã…Â¸lÃƒâ€Ã‚Â±k stilini uygula
    \chapter*{\ozgecmisname} % BaÃƒâ€¦Ã…Â¸lÃƒâ€Ã‚Â±k (numarasÃƒâ€Ã‚Â±z)
    
    \addtocontents{toc}{\protect\addvspace{-10\p@}} % ToC'ye boÃƒâ€¦Ã…Â¸luk ekle
    \addcontentsline{toc}{chapter}{\bf{\protect\ozgecmisnameToC}}
    % BaÃƒâ€¦Ã…Â¸lÃƒâ€Ã‚Â±k sayfasÃƒâ€Ã‚Â±nÃƒâ€Ã‚Â± ToC'ye ekle
    \@mkboth{\MakeUppercase\ozgecmisname}{\MakeUppercase\ozgecmisname} % Sayfa baÃƒâ€¦Ã…Â¸lÃƒâ€Ã‚Â±klarÃƒâ€Ã‚Â±nÃƒâ€Ã‚Â± ekle
    \singlespacing % Tek aralÃƒâ€Ã‚Â±klÃƒâ€Ã‚Â± yazÃƒâ€Ã‚Â±
    \sloppy % SatÃƒâ€Ã‚Â±r sonu dÃƒÆ’Ã‚Â¼zeni
    \th@ozgecmisStash % Ãƒâ€Ã‚Â°ÃƒÆ’Ã‚Â§eriÃƒâ€Ã…Â¸i buraya yerleÃƒâ€¦Ã…Â¸tir
}



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% \renewcommand\tableofcontents{
%          \vspace*{\ChapterUstenBosluk}
%              {\chapter*{\contentsname}\addcontentsline{toc}{chapter}{\bf{\protect\contentsnameToC}}% AKC
%     \vspace*{-20pt}
%     \hfill\vspace*{0.5truecm}{\bf\underline{\if@Ingilizce Page\else Sayfa\fi}}}

%     \let\orig@numberline\numberline
%     \@mkboth{\MakeUppercase\listtablename}{\MakeUppercase\listtablename}
%     \newlength{\th@oldparskip}
%     \setlength{\th@oldparskip}{\parskip}
%     \setlength{\parskip}{\ToCparskip}
%     \@starttoc{toc}
%     \setlength{\parskip}{\th@oldparskip}
%     }
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  
\newcommand\kisaltmalist{
    \vspace*{\ChapterUstenBosluk}
    \chapter*{\kisaltmaname\@mkboth{\MakeUppercase\kisaltmaname}{\MakeUppercase\kisaltmaname}}
    \addtocontents{toc}{\protect\addvspace{-10\p@}} %AKC
    \addcontentsline{toc}{chapter}{\bf{\protect\kisaltmanameToC}} %AKC
    \oneandonehalf
    \noindent\th@kisaltmalistStash\par}
    
 %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  
\newcommand\symbollist{
    \vspace*{\ChapterUstenBosluk}
    \chapter*{\symbolname\@mkboth{\MakeUppercase\symbolname}{\MakeUppercase\symbolname}}
    \addtocontents{toc}{\protect\addvspace{-10\p@}} %AKC
    \addcontentsline{toc}{chapter}{\bf{\protect\symbolnameToC}} %AKC
    \oneandonehalf
    \noindent\th@symbollistStash\par
    }
\newcommand\simgelervekisaltmalist{
    \vspace*{\ChapterUstenBosluk}
    \chapter*{\symbolname\@mkboth{\MakeUppercase\symbolname}{\MakeUppercase\symbolname}}
    \addtocontents{toc}{\protect\addvspace{-10\p@}} %AKC
    \addcontentsline{toc}{chapter}{\bf{\protect\symbolnameToC}} %AKC
    \oneandonehalf
    \if@SembolListesiVar
      \noindent\th@symbollistStash\par
    \fi
    \if@KisaltmaListesiVar
      \if@SembolListesiVar\vspace*{8mm}\fi
      \noindent\th@kisaltmalistStash\par
    \fi
    }
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% APPENDIX command

\newcommand{\eklerbolum}[1]{\par
    \newpage
    \singlespacing
    \setcounter{chapter}{#1}%
    \setcounter{section}{0}%
	 \renewcommand\thechapter{EK-\arabic{chapter}}
	 \renewcommand{\theequation}{\thechapter.\arabic{equation}}
	 \renewcommand{\thefigure}{\thechapter.\arabic{figure}}
	 \renewcommand{\thetable}{\thechapter.\arabic{table}}
	 \setcounter{equation}{0}
    %\renewcommand\@chapapp{\appendixname}%
              %\addtocontents{toc}{\protect\addvspace{-10\p@}}
%    \addcontentsline{toc}{chapter}{\bf{\protect\appendixnameToC}}
    \global \@appendixtrue
    }
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\renewcommand{\@biblabel}[1]{#1}
\renewenvironment{thebibliography}[1]{%\singlespacing
     \chapter*{\bibname}%
     \oneandonehalf
     \addtocontents{toc}{\protect\addvspace{-10\p@}}
     \addcontentsline{toc}{chapter}{\bf{\protect\bibnameToC}}
     \@mkboth{\MakeUppercase\bibname}{\MakeUppercase\bibname}%
     \list{\@biblabel{[\@arabic\c@enumiv]}}%
           {\settowidth\labelwidth{\@biblabel{999}}%
            \leftmargin\labelwidth
            \advance\leftmargin\labelsep
            \setlength{\leftmargin}{-\leftmargin}
            \advance\leftmargin by 29.0mm
            \setlength{\itemindent}{-15.0mm}%
  %         \setlength{\listparindent}{-20mm}%
            \@openbib@code
            \usecounter{enumiv}%
            \let\p@enumiv\@empty
            \renewcommand\theenumiv{\@arabic\c@enumiv}}%
      \sloppy
      \clubpenalty4000
      \@clubpenalty \clubpenalty
      \widowpenalty4000%
      \sfcode`\.\@m}
     {\def\@noitemerr
       {\@latex@warning{Empty `thebibliography' environment}}%
      \endlist}
      
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\renewcommand{\th@onaypage}{
    \thispagestyle{empty}
    \BolumSagdaKalsin
    \singlespacing
    \hyphenpenalty=5000
    \vspace*{18mm}
    \begin{center}
      {\th@ChapterStyle KABUL VE ONAY}
    \end{center}
    \vspace*{8mm}
    \noindent \th@isimsoyisim, İnönü Üniversitesi \th@Enstitu{}
    \th@ogrencino{} numaralı \if@Doktora doktora\else yüksek lisans\fi{}
    öğrencisi olarak, ``\Baslikbir{} \Baslikiki{} \Baslikuc{}''
    başlıklı tezini jüri önünde başarı ile sunmuştur.

    \vspace*{12mm}
    \noindent\begin{tabular*}{\textwidth}{@{}p{40mm}p{78mm}@{\extracolsep{\fill}}p{32mm}@{}}
    Tez Danışmanı: & \textbf{\th@TezYoneticisi} & \th@ImzaCizgisi \\
     & \th@TezYoneticisiUniv & \\
    \ifthenelse{\equal{\th@esdanisman}{}}{}{Eş Danışman: & \textbf{\th@esdanisman} & \th@ImzaCizgisi \\
     & \th@esdanismanuniv & \\}
    Jüri Üyeleri: & \textbf{\th@juribir} & \th@ImzaCizgisi \\
     & \th@juribiruniv & \\
     & \textbf{\th@juriiki} & \th@ImzaCizgisi \\
     & \th@juriikiuniv & \\
     & \textbf{\th@juriuc} & \th@ImzaCizgisi \\
     & \th@juriucuniv & \\
    \ifthenelse{\equal{\th@juridort}{}}{}{ & \textbf{\th@juridort} & \th@ImzaCizgisi \\
     & \th@juridortuniv & \\}
    \ifthenelse{\equal{\th@juribes}{}}{}{ & \textbf{\th@juribes} & \th@ImzaCizgisi \\
     & \th@juribesuniv & \\}
    \end{tabular*}

    \vspace*{8mm}
    \noindent Teslim Tarihi: \textbf{\th@tezvermetarih}\hfill
    Savunma Tarihi: \textbf{\th@tezsavunmatarih}

    \vspace*{8mm}
    \noindent Bu tez, jüri üyeleri tarafından \textbf{\th@oy} ile kabul edilmiş
    ve Enstitü Yönetim Kurulu'nun \textbf{\th@yonetimkurulutarih} tarihli,
    \textbf{\th@yonetimkurulukararno} sayılı kararı ile onaylanmıştır.

    \vfill
    \begin{center}
    \ifthenelse{\equal{\th@EnstituMuduru}{}}{}{\textbf{\th@EnstituMuduru}\\ Enstitü Müdürü}
    \end{center}
}

\newcommand{\th@MakeThesisPrologue}{
        \thispagestyle{empty}
        \sffamily
        \selectfont
        \setboolean{@twoside}{false} %AKC: Temporarily move to one-sided mode
        \th@Kapak
        \if@Onluarkali
            \setboolean{@twoside}{false} % 2025 kilavuzunda on bolum ardil akar.
        \fi
        \normalfont\selectfont
        \pagenumbering{roman}%
%        \setcounter{page}{\if@Bez 3\else 1\fi}%{\if@Ingilizce\if@Bez 3\else 1\fi\else 1\fi}
        \setcounter{page}{3}
        \th@PageNumberBottomRight
        \singlespacing
		  \ifPDFTeX\renewcommand{\ttdefault}{pcr}\fi
		  \normalfont\selectfont	       %MS Times fontu iÃƒÆ’Ã‚Â§in
         

        \th@EtikBeyanSayfasi
        \ifthenelse{\equal{\th@Ithaf}{}}{}{\th@IthafSayfasi} 
        \ToCspacing
        \BolumSagdaKalsin
        {%
        \let\ps@plain\ps@empty
        \pagestyle{empty}
        \tableofcontents
        \clearpage
        }%
        \pagestyle{fancy}
        \th@PageNumberBottomRight
        \singlespacing
        \if@TesekkurVar
	  \th@Onsoz
        \fi
        \if@Ingilizce
	      \th@Summarypage
	      \th@ozetpage
	    \else
	      \th@ozetpage
	      \th@Summarypage
	\fi
        \if@SembolListesiVar
	  \simgelervekisaltmalist
        \else
          \if@KisaltmaListesiVar
	    \simgelervekisaltmalist
          \fi
        \fi
        \if@SekilListesiVar
          \BolumSagdaKalsin
	      \LoFspacing
	  
	      \listoffigures
	      \addtocontents{toc}{\protect\addvspace{-11\p@}} %AKC
	      \addcontentsline{toc}{chapter}{\bf{\protect\listfigurenameToC}}	  
        \fi
        \if@TabloListesiVar
          \BolumSagdaKalsin
	      \LoTspacing
	  
	      \listoftables
	      \addtocontents{toc}{\protect\addvspace{-11\p@}} %AKC
	      \addcontentsline{toc}{chapter}{\bf{\protect\listtablenameToC}}
        \fi
        \if@Onluarkali
            \setboolean{@twoside}{true}
        \fi
        \newpage
	\BolumSagdaKalsinNolu
        \oneandonehalf
     }


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 2025 Word şablonu kapak/onay/etik son geçersiz kılmaları
\newcommand*{\th@OnayLogo}{%
  \IfFileExists{iu_logo_yellow.png}{%
    \includegraphics[height=12.5mm]{iu_logo_yellow.png}%
  }{%
    \IfFileExists{kabul-onay-logo.jpeg}{%
      \includegraphics[height=12.5mm]{kabul-onay-logo.jpeg}%
    }{%
      \IfFileExists{iu_logo.png}{%
        \includegraphics[height=12.5mm]{iu_logo.png}%
      }{%
        \IfFileExists{assets/inonu-logo.png}{%
          \includegraphics[height=12.5mm]{assets/inonu-logo.png}%
        }{}%
      }%
    }%
  }%
}
\newcommand*{\th@OnayUstBilgi}{%
  \noindent\begingroup
  \setlength{\unitlength}{1mm}%
  \linethickness{0.4pt}%
  \makebox[\textwidth][l]{%
    \begin{picture}(168,26)
      \put(0,0){\framebox(168,26){}}
      \put(36,0){\line(0,1){26}}
      \put(104,0){\line(0,1){26}}
      \put(134,0){\line(0,1){26}}
      \put(0,4.2){\line(1,0){36}}
      \put(0,9.8){\line(1,0){36}}
      \put(104,6.5){\line(1,0){64}}
      \put(104,13){\line(1,0){64}}
      \put(104,19.5){\line(1,0){64}}
      \put(0,9.8){\makebox(36,16.2){\th@OnayLogo}}
      \put(0,4.2){\makebox(36,5.6){\bfseries\fontsize{8.5}{10}\selectfont İNÖNÜ ÜNİVERSİTESİ}}
      \put(36,0){\makebox(68,26){\bfseries\fontsize{12}{14}\selectfont KABUL ONAY FORMU}}
      \put(106,19.5){\makebox(28,6.5)[l]{\fontsize{10.5}{12}\selectfont Doküman No}}
      \put(134,19.5){\makebox(34,6.5){\fontsize{10.5}{12}\selectfont İNÜ-KYS-FRM-142}}
      \put(106,13){\makebox(28,6.5)[l]{\fontsize{10.5}{12}\selectfont Yayın Tarihi}}
      \put(134,13){\makebox(34,6.5){\fontsize{10.5}{12}\selectfont 19.08.2019}}
      \put(106,6.5){\makebox(28,6.5)[l]{\fontsize{10.5}{12}\selectfont Revizyon No}}
      \put(106,0){\makebox(28,6.5)[l]{\fontsize{10.5}{12}\selectfont Revizyon Tarihi}}
    \end{picture}%
  }%
  \endgroup
}
\renewcommand{\th@onaypage}{%
  \thispagestyle{empty}%
  \enlargethispage{16mm}%
  \sffamily\fontsize{11}{14.5}\selectfont%
  \vspace*{-14mm}%
  \th@OnayUstBilgi
  \vspace*{4mm}
  \begin{center}
    {\bfseries\fontsize{14}{17}\selectfont İNÖNÜ ÜNİVERSİTESİ\par}
    {\bfseries\fontsize{14}{17}\selectfont FEN BİLİMLERİ ENSTİTÜSÜ MÜDÜRLÜĞÜ\par}
    \vspace*{13mm}{\bfseries\fontsize{12.5}{15}\selectfont \th@FullTitle\par}
    \vspace*{5mm}{\bfseries \TezSeviyesi\par}
    \vspace*{7mm}
    \ifthenelse{\equal{\th@esdanisman}{}}{%
      \begin{tabular}{p{65mm}p{65mm}}\centering\bfseries DANIŞMAN & \centering\arraybackslash\bfseries HAZIRLAYAN\\[3mm]
      \centering\bfseries \th@TezYoneticisi & \centering\arraybackslash\bfseries \th@isimsoyisim\end{tabular}}
    {\begin{tabular}{p{44mm}p{54mm}p{44mm}}\centering\bfseries DANIŞMAN & \centering\bfseries İKİNCİ TEZ DANIŞMANI & \centering\arraybackslash\bfseries HAZIRLAYAN\\[3mm]
      \centering\bfseries \th@TezYoneticisi & \centering\bfseries \th@esdanisman & \centering\arraybackslash\bfseries \th@isimsoyisim\end{tabular}}
  \end{center}
  \vspace*{7mm}
  \noindent Jürimiz tarafından \dotfill/\dotfill/20\dotfill{} tarihinde yapılan tez savunma sınavı sonucunda bu tez
  \textbf{oybirliği / oyçokluğu} ile başarılı bulunarak \dotfill{} Anabilim Dalı \TezSeviyesi{} olarak kabul etmiştir.
  \vspace*{4mm}
  \noindent\begin{tabular*}{\textwidth}{@{}p{123mm}@{\extracolsep{\fill}}p{35mm}@{}}
  \textbf{Jüri Üyelerinin Unvanı Adı Soyadı} & \textbf{İmza}\\[1.5mm]
  \th@OnayJuriSatiri{1}{\th@juribir}
  \th@OnayJuriSatiri{2}{\th@juriiki}
  \th@OnayJuriSatiri{3}{\th@juriuc}
  \th@OnayJuriSatiri{4}{\th@juridort}
  \th@OnayJuriSatiri{5}{\th@juribes}
  \end{tabular*}
  \vspace*{4mm}
  \begin{center}{\bfseries O\ \ N\ \ A\ \ Y}\end{center}
  \noindent Bu tez, İnönü Üniversitesi Lisansüstü Eğitim-Öğretim Yönetmeliği'nin ilgili maddeleri uyarınca
  yukarıdaki jüri üyeleri tarafından kabul edilmiş ve Enstitü Yönetim Kurulu'nun \dotfill/\dotfill/20\dotfill{} tarih ve
  20\dotfill/\dotfill{} sayılı Kararıyla da uygun görülmüştür.
  \vspace*{3mm}
  \begin{center}\ifthenelse{\equal{\th@EnstituMuduru}{}}{\dotfill}{\bfseries\th@EnstituMuduru\\Enstitü Müdürü}\end{center}
}
\renewcommand{\th@EtikBeyanSayfasi}{%
     \BolumSagdaKalsinNolu
     \thispagestyle{empty}
     \sffamily\fontsize{11}{16.5}\selectfont
     \oneandonehalf
     \sloppy\setlength{\emergencystretch}{3em}
     \vspace*{-6mm}
     \begin{center}
     {\bfseries T.C.\\ İNÖNÜ ÜNİVERSİTESİ\\ FEN BİLİMLERİ ENSTİTÜSÜ MÜDÜRLÜĞÜNE\par}
     \vspace*{5mm}
     {\bfseries ETİK VE YAPAY ZEK\^A KULLANIM BEYANI\par}
     \end{center}
     \vspace*{3mm}
     \noindent \dotfill/\dotfill/20\dotfill
     \vspace*{3mm}
     \noindent İnönü Üniversitesi Lisansüstü Tez Yazım Kurallarına uygun olarak, ``\th@TezYoneticisi'' danışmanlığında hazırlayıp sunduğum ``\th@FullTitle'' başlıklı \if@Doktora doktora\else yüksek lisans\fi{} tezinde;
     \vspace*{2mm}
     \noindent\textbf{1. ETİK VE BİLİMSEL SORUMLULUKLARIM:}
     \begin{itemize}\setlength\itemsep{0pt}
       \item Tezimde yer alan verileri, bilgileri ve belgeleri akademik ve etik kurallar çerçevesinde elde ettiğimi, değerlendirdiğimi ve sonuçları bilimsel etik ve ahlak kurallarına uygun olarak sunduğumu,
       \item Çalışmada yararlandığım tüm kaynaklara bilimsel kurallara uygun şekilde atıfta bulunduğumu ve kaynak gösteriminde APA 7. baskı kurallarına uyduğumu,
       \item Tezimin özgün olduğunu, çalışma ve yazım sürecinde patent ve telif haklarını ihlal edici hiçbir davranışta bulunmadığımı,
       \item Aksi bir durumda doğabilecek tüm hukuki ve akademik sonuçları kabul ettiğimi,
     \end{itemize}
     \noindent\textbf{2. YAPAY ZEK\^A KULLANIMINA İLİŞKİN BEYANIM:}
     \noindent (\IfStrEq{\th@yapayzekakullanimi}{hayir}{X}{ }) Tez yazım sürecinde yapay zek\^a tabanlı araçlardan faydalanmadım.\\
     (\IfStrEq{\th@yapayzekakullanimi}{evet}{X}{ }) Tez yazım sürecinde yapay zek\^a tabanlı araçlardan faydalandım.
     \begin{itemize}\setlength\itemsep{0pt}
       \item Yapay zek\^a araçlarını yalnızca bilimsel üretim sürecini desteklemek amacıyla kullandığımı,
       \item Kullanımın hipotez geliştirme, teorik tartışma ve yorumlama gibi üst düzey akademik becerileri içermediğini,
       \item Kullanımın tezin özgünlüğüne, bilimsel etik kurallarına ve ilgili mevzuata aykırı olmadığını,
       \item Usulsüz kullanımlara kesinlikle başvurmadığımı,
       \item Kullanılan yapay zek\^a araçlarının ve işlevlerinin, danışmanımın bilgisi dâhilinde, ekte verilen tabloda şeffaf biçimde belirtildiğini,
       \item Yükseköğretim Kurulu Bilimsel Araştırma ve Yayın Faaliyetlerinde Üretken Yapay Zek\^a Kullanımına Dair Etik Rehber'de belirtilen ilkelere riayet ettiğimi
     \end{itemize}
     \noindent kabul ve taahhüt ederim.\par
     \vspace*{6mm}
     \noindent Öğrencinin Adı Soyadı: \th@isimsoyisim\par
     \noindent İmza: \makebox[70mm]{\dotfill}\par
     \IfStrEq{\th@yapayzekakullanimi}{evet}{\vspace*{4mm}\noindent\textbf{EK: Yapay Zek\^a Kullanım Tablosu}\par\th@yapayzekatablosu}{}
}
\let\th@OldBeginDocument\document
\renewcommand*{\document}{
    \th@OldBeginDocument
    \if@SirtKapak
      \th@SirtKapak
    \else
      \th@MakeThesisPrologue
      \oneandonehalf
      \th@PageNumberBottomCenter
      \pagenumbering{arabic}
    \fi
}

\endinput
