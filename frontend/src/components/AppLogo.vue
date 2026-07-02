<template>
  <!--
    36×36 viewBox
    C arc: center (18,18), radius 9.5, gap ±55° on right side
    ECG pulse: baseline at y=18, blip in center, exits through C gap on right
  -->
  <svg
    viewBox="0 0 36 36"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style="display:block;width:100%;height:100%"
    aria-hidden="true"
  >
    <!-- C arc -->
    <path
      d="M 23.5,10.2 A 9.5,9.5 0 1,0 23.5,25.8"
      stroke="white"
      stroke-width="3"
      stroke-linecap="round"
      fill="none"
    />
    <!-- ECG pulse line — enters left, blips in center, exits through C gap -->
    <polyline
      points="4.5,18 9,18 11,13 14,24 16.5,18 28,18"
      stroke="white"
      stroke-width="1.7"
      stroke-linecap="round"
      stroke-linejoin="round"
      fill="none"
      opacity="0.88"
    />
    <!-- Blip peak dot -->
    <circle cx="11" cy="13" r="1.8" fill="white" opacity="0.7"/>
  </svg>
</template>
