#include <stdio.h>
#include <stdint.h>
#include <emmintrin.h>
#include <wmmintrin.h>
static uint64_t ref(uint64_t a,uint64_t b,int hi){
  uint64_t l=0,h=0;
  for(int i=0;i<64;i++) if((b>>i)&1){ l^=(i?a<<i:a); h^=(i?a>>(64-i):0); }
  return hi?h:l;
}
int main(void){
  uint64_t v[]={0,1,2,3,0x8000000000000000ULL,~0ULL,0xAAAAAAAAAAAAAAAAULL,0x856d9c28a9741a02ULL};
  for(int i=0;i<8;i++)for(int j=0;j<8;j++){
    uint64_t a=v[i],b=v[j];
    __m128i P=_mm_clmulepi64_si128(_mm_cvtsi64_si128((long long)a),
                                   _mm_cvtsi64_si128((long long)b),0x00);
    uint64_t lo=(uint64_t)_mm_cvtsi128_si64(P);
    uint64_t hi=(uint64_t)_mm_cvtsi128_si64(_mm_srli_si128(P,8));
    if(lo!=ref(a,b,0)||hi!=ref(a,b,1)){
      printf("FAIL a=%016llx b=%016llx got %016llx/%016llx want %016llx/%016llx\n",
        (unsigned long long)a,(unsigned long long)b,(unsigned long long)lo,(unsigned long long)hi,
        (unsigned long long)ref(a,b,0),(unsigned long long)ref(a,b,1)); return 1; }
  }
  puts("clmul ok"); return 0;
}