import './product-detail.scss'
import Reviews from './modules/reviews/reviews'

function init() {
  Reviews()
  // Product detail
  $('.product-links-wap a').click(function () {
    var this_src = $(this).children('img').attr('src')
    $('#product-detail').attr('src', this_src)
    return false
  })
  $('#btn-minus').click(function () {
    var val = $('#var-value').html()
    val = val == '1' ? val : val - 1
    $('#var-value').html(val)
    $('#product-quanity').val(val)
    return false
  })
  $('#btn-plus').click(function () {
    var val = $('#var-value').html()
    val++
    $('#var-value').html(val)
    $('#product-quanity').val(val)
    return false
  })
  $('.btn-size').click(function () {
    var this_val = $(this).html()
    $('#product-size').val(this_val)
    $('.btn-size').removeClass('btn-secondary')
    $('.btn-size').addClass('btn-success')
    $(this).removeClass('btn-success')
    $(this).addClass('btn-secondary')
    return false
  })
  const carousel = $('#carousel-related-product')
  if (carousel.length) {
    let maxHeight = 0
    carousel.find('.carousel-item').each(function () {
      const itemHeight = $(this).outerHeight()
      if (itemHeight > maxHeight) {
        maxHeight = itemHeight
      }
    })
    carousel
      .find('.carousel-inner, .carousel-item')
      .css('min-height', maxHeight + 'px')
  }
}

export default init
