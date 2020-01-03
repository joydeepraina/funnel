import { Utils, ScrollActiveMenu, LazyloadImg } from './util';

$(() => {
  window.HasGeek = {};
  window.HasGeek.config = {
    mobileBreakpoint: 768, // this breakpoint switches to desktop UI
    ajaxTimeout: 30000,
    retryInterval: 10000,
    closeModalTimeout: 10000,
  };

  Utils.collapse();
  Utils.smoothScroll();
  Utils.scrollTabs();
  Utils.navSearchForm();

  const intersectionObserverComponents = function() {
    if (document.querySelector('#page-navbar')) {
      ScrollActiveMenu.init(
        'page-navbar',
        'sub-navbar__item',
        'sub-navbar__item--active'
      );
    }
    LazyloadImg.init('js-lazyload-img');
  };

  if (
    document.querySelector('#page-navbar') ||
    document.querySelector('.js-lazyload-img') ||
    document.querySelector('.js-lazyload-results')
  ) {
    if (
      !(
        'IntersectionObserver' in global &&
        'IntersectionObserverEntry' in global &&
        'intersectionRatio' in IntersectionObserverEntry.prototype
      )
    ) {
      const polyfill = document.createElement('script');
      polyfill.setAttribute('type', 'text/javascript');
      polyfill.setAttribute(
        'src',
        'https://cdn.polyfill.io/v2/polyfill.min.js?features=IntersectionObserver'
      );
      polyfill.onload = function() {
        intersectionObserverComponents();
      };
      document.head.appendChild(polyfill);
    } else {
      intersectionObserverComponents();
    }
  }

  if (!('URLSearchParams' in window)) {
    const polyfill = document.createElement('script');
    polyfill.setAttribute('type', 'text/javascript');
    polyfill.setAttribute(
      'src',
      'https://cdnjs.cloudflare.com/ajax/libs/url-search-params/1.1.0/url-search-params.js'
    );
    document.head.appendChild(polyfill);
  }

  // Send click events to Google analytics
  $('.mui-btn, a').click(function gaHandler() {
    const action =
      $(this).attr('data-action') || $(this).attr('title') || $(this).html();
    const target = $(this).attr('href') || '';
    Utils.sendToGA('click', action, target);
  });

  $('.js-truncate').each(function() {
    let linesLimit = $(this).data('truncate-lines');
    $(this).trunk8({
      lines: linesLimit,
    });
  });

  $('.js-truncate-readmore').each(function() {
    let linesLimit = $(this).data('truncate-lines');
    $(this).trunk8({
      lines: linesLimit,
      fill:
        '&hellip;<span class="js-read-more mui--text-hyperlink read-more">read more</span>',
    });
  });

  $('.js-read-more').click(function() {
    $(this)
      .parent('.js-truncate-readmore')
      .trunk8('revert');
  });
});
