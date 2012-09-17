      program psort
      include 'pipe1.inc'
      integer N
      character*80 desfile, junk, tag
      integer*4 idescol(MAXCOL)
      parameter (N=10000000)
      integer  myindex(N),tagcol, i,j,k
      real*8 arr(N)
c check for descriptor file in command line
      call getcmdchar('des',1,'optional',ifound, desfile)

      if( ifound .eq. 1 ) then
c if des found, read from unit 7
         iunit=7
      else
c else, get descriptor from standard input
         iunit=5
      endif
      call pdesread(iunit, desfile,  cdesheader,
     &               cdesstitle,  cdesltitle,
     &                ndeslines)

c check for nodes keyword in command line
      call getcmdchar('nodes',0,'optional',ifound, junk)
      
      if (ifound.eq.0) then
c if not present, send descriptor file down pipe
        call pdeswrite(6, cdesname, cdesheader,
     &               cdesstitle,  cdesltitle,
     &               ndeslines)
       endif

      call getcmdchar('sort',1,'required',ifound, tag)

      call findcol(tag,cdesstitle,ndeslines, tagcol)

c      write (0,*) 'tagcol= ', tagcol

      if (tagcol.eq.0) stop 
     & 'psort error: tag not supplied'

c check command line for bogus key words
      call chkcmdkey('bogus')


      j=0
      k=0

      open (unit=2, status='scratch', form='unformatted', 
     &      access='direct', recl=ndeslines*8)


10    ios = read5(rdat, ndeslines)
      if( ios .eq. -1 ) goto 999

      j=j+1
      arr(j)=rdat(tagcol)
      myindex(j)=j
c      write (0,*) j,arr(j)

      if (arr(j).gt.k) then
         k=arr(j)
      endif
      
      write (2, rec=j) (rdat(i), i=1,ndeslines)


      if (j.gt.n) stop 'psort error: maximum lines exceeded'
      goto 10
999   continue

      if (j.eq.1) then
         write(0,*) "No data to sort."
         goto 90
      endif


c      write(0,*) 'Number of entries is:', j
c      write(0,*) 'Number of bins is: ', k

c      write (0,*) 'calling sortx2'
      call sortrx(j,arr,myindex)
c      write (0,*) 'called sortx2'

c      do ii=1,j
c         write (0,*) ii,myindex(ii)
c      enddo
c     Writes the data out in the order of the sorted myindex array to the main file
      do i=1,j
         i1=myindex(i)
         read(2,rec=i1) (rdat(l),l=1,ndeslines)
c         write (0,*) (rdat(l),l=1,ndeslines)
         ios=write6(rdat,ndeslines) 
      enddo



c      do i=1,j
c        write(0,*) i,arr(i),myindex(i)
c      enddo      

 90   close(2)
      endfile ( unit=6)
      ios=close5()
      stop
      end


      

c************************************************************

c******************************************************************
c*****************************************************************

C From Leonard J. Moss of SLAC:

C Here's a hybrid QuickSort I wrote a number of years ago.  It's
C based on suggestions in Knuth, Volume 3, and performs much better
C than a pure QuickSort on short or partially ordered input arrays.  

      SUBROUTINE SORTRX(N,DATA,MYINDEX)
C===================================================================
C
C     SORTRX -- SORT, Real input, myindex output
C
C
C     Input:  N     INTEGER
C             DATA  REAL
C
C     Output: MYINDEX INTEGER (DIMENSION N)
C
C This routine performs an in-memory sort of the first N elements of
C array DATA, returning into array MYINDEX the indices of elements of
C DATA arranged in ascending order.  Thus,
C
C    DATA(MYINDEX(1)) will be the smallest number in array DATA;
C    DATA(MYINDEX(N)) will be the largest number in DATA.
C
C The original data is not physically rearranged.  The original order
C of equal input values is not necessarily preserved.
C
C===================================================================
C
C SORTRX uses a hybrid QuickSort algorithm, based on several
C suggestions in Knuth, Volume 3, Section 5.2.2.  In particular, the
C "pivot key" [my term] for dividing each subsequence is chosen to be
C the median of the first, last, and middle values of the subsequence;
C and the QuickSort is cut off when a subsequence has 9 or fewer
C elements, and a straight insertion sort of the entire array is done
C at the end.  The result is comparable to a pure insertion sort for
C very short arrays, and very fast for very large arrays (of order 12
C micro-sec/element on the 3081K for arrays of 10K elements).  It is
C also not subject to the poor performance of the pure QuickSort on
C partially ordered data.
C
C Created:  15 Jul 1986  Len Moss
C
C===================================================================
 
      implicit real*8 (a-h,o-z)
      INTEGER   N,MYINDEX(N)
      REAL*8      DATA(N)
 
      INTEGER   LSTK(31),RSTK(31),ISTK
      INTEGER   L,R,I,J,P,MYINDEXP,MYINDEXT
      REAL*8      DATAP
 
C     QuickSort Cutoff
C
C     Quit QuickSort-ing when a subsequence contains M or fewer
C     elements and finish off at end with straight insertion sort.
C     According to Knuth, V.3, the optimum value of M is around 9.
 
      INTEGER   M
      PARAMETER (M=9)
 
C===================================================================
C
C     Make initial guess for MYINDEX
 
      DO 50 I=1,N
         MYINDEX(I)=I
 50          CONTINUE
 
C     If array is short, skip QuickSort and go directly to
C     the straight insertion sort.
 
      IF (N.LE.M) GOTO 900
 
C===================================================================
C
C     QuickSort
C
C     The "Qn:"s correspond roughly to steps in Algorithm Q,
C     Knuth, V.3, PP.116-117, modified to select the median
C     of the first, last, and middle elements as the "pivot
C     key" (in Knuth's notation, "K").  Also modified to leave
C     data in place and produce an MYINDEX array.  To simplify
C     comments, let DATA[I]=DATA(MYINDEX(I)).
 
C Q1: Initialize
      ISTK=0
      L=1
      R=N
 
 200   CONTINUE
 
C Q2: Sort the subsequence DATA[L]..DATA[R].
C
C     At this point, DATA[l] <= DATA[m] <= DATA[r] for all l < L,
C     r > R, and L <= m <= R.  (First time through, there is no
C     DATA for l < L or r > R.)
 
      I=L
      J=R
 
C Q2.5: Select pivot key
C
C     Let the pivot, P, be the midpoint of this subsequence,
C     P=(L+R)/2; then rearrange MYINDEX(L), MYINDEX(P), and MYINDEX(R)
C     so the corresponding DATA values are in increasing order.
C     The pivot key, DATAP, is then DATA[P].
 
      P=(L+R)/2
      MYINDEXP=MYINDEX(P)
      DATAP=DATA(MYINDEXP)
 
      IF (DATA(MYINDEX(L)) .GT. DATAP) THEN
         MYINDEX(P)=MYINDEX(L)
         MYINDEX(L)=MYINDEXP
         MYINDEXP=MYINDEX(P)
         DATAP=DATA(MYINDEXP)
      ENDIF
 
      IF (DATAP .GT. DATA(MYINDEX(R))) THEN
         IF (DATA(MYINDEX(L)) .GT. DATA(MYINDEX(R))) THEN
            MYINDEX(P)=MYINDEX(L)
            MYINDEX(L)=MYINDEX(R)
         ELSE
            MYINDEX(P)=MYINDEX(R)
         ENDIF
         MYINDEX(R)=MYINDEXP
         MYINDEXP=MYINDEX(P)
         DATAP=DATA(MYINDEXP)
      ENDIF
 
C     Now we swap values between the right and left sides and/or
C     move DATAP until all smaller values are on the left and all
C     larger values are on the right.  Neither the left or right
C     side will be internally ordered yet; however, DATAP will be
C     in its final position.
 
 300   CONTINUE
 
C Q3: Search for datum on left >= DATAP
C
C     At this point, DATA[L] <= DATAP.  We can therefore start scanning
C     up from L, looking for a value >= DATAP (this scan is guaranteed
C     to terminate since we initially placed DATAP near the middle of
C     the subsequence).
 
         I=I+1
         IF (DATA(MYINDEX(I)).LT.DATAP) GOTO 300
 
 400      CONTINUE
 
C Q4: Search for datum on right <= DATAP
C
C     At this point, DATA[R] >= DATAP.  We can therefore start scanning
C     down from R, looking for a value <= DATAP (this scan is guaranteed
C     to terminate since we initially placed DATAP near the middle of
C     the subsequence).
 
         J=J-1
         IF (DATA(MYINDEX(J)).GT.DATAP) GOTO 400
 
C Q5: Have the two scans collided?
 
      IF (I.LT.J) THEN
 
C Q6: No, interchange DATA[I] <--> DATA[J] and continue
 
         MYINDEXT=MYINDEX(I)
         MYINDEX(I)=MYINDEX(J)
         MYINDEX(J)=MYINDEXT
         GOTO 300
      ELSE
 
C Q7: Yes, select next subsequence to sort
C
C     At this point, I >= J and DATA[l] <= DATA[I] == DATAP <= DATA[r],
C     for all L <= l < I and J < r <= R.  If both subsequences are
C     more than M elements long, push the longer one on the stack and
C     go back to QuickSort the shorter; if only one is more than M
C     elements long, go back and QuickSort it; otherwise, pop a
C     subsequence off the stack and QuickSort it.
 
         IF (R-J .GE. I-L .AND. I-L .GT. M) THEN
            ISTK=ISTK+1
            LSTK(ISTK)=J+1
            RSTK(ISTK)=R
            R=I-1
         ELSE IF (I-L .GT. R-J .AND. R-J .GT. M) THEN
            ISTK=ISTK+1
            LSTK(ISTK)=L
            RSTK(ISTK)=I-1
            L=J+1
         ELSE IF (R-J .GT. M) THEN
            L=J+1
         ELSE IF (I-L .GT. M) THEN
            R=I-1
         ELSE
C Q8: Pop the stack, or terminate QuickSort if empty
            IF (ISTK.LT.1) GOTO 900
            L=LSTK(ISTK)
            R=RSTK(ISTK)
            ISTK=ISTK-1
         ENDIF
         GOTO 200
      ENDIF
 
 900   CONTINUE
 
C===================================================================
C
C Q9: Straight Insertion sort
 
      DO 950 I=2,N
         IF (DATA(MYINDEX(I-1)) .GT. DATA(MYINDEX(I))) THEN
            MYINDEXP=MYINDEX(I)
            DATAP=DATA(MYINDEXP)
            P=I-1
 920               CONTINUE
               MYINDEX(P+1) = MYINDEX(P)
               P=P-1
               IF (P.GT.0) THEN
                  IF (DATA(MYINDEX(P)).GT.DATAP) GOTO 920
               ENDIF
            MYINDEX(P+1) = MYINDEXP
         ENDIF
 950         CONTINUE
 
C===================================================================
C
C     All done
 
      END


