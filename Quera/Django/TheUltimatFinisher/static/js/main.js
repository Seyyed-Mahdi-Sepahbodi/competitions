// Main JavaScript for Dynamic Form Builder

$(document).ready(() => {
  // Initialize tooltips
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  var tooltipList = tooltipTriggerList.map((tooltipTriggerEl) => new window.bootstrap.Tooltip(tooltipTriggerEl))

  // Initialize popovers
  var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
  var popoverList = popoverTriggerList.map((popoverTriggerEl) => new window.bootstrap.Popover(popoverTriggerEl))

  // Auto-hide alerts after 5 seconds
  $(".alert:not(.alert-permanent)").delay(5000).fadeOut("slow")


  // Form validation enhancement
  $("form").on("submit", function () {
    var $form = $(this)
    var $submitBtn = $form.find('button[type="submit"]')

    // Disable submit button to prevent double submission
    $submitBtn.prop("disabled", true)
    $submitBtn.html('<i class="fas fa-spinner fa-spin me-2"></i>Processing...')

    // Re-enable after 3 seconds as fallback
    setTimeout(() => {
      $submitBtn.prop("disabled", false)
      $submitBtn.html($submitBtn.data("original-text") || "Submit")
    }, 3000)
  })

  // Store original button text
  $('button[type="submit"]').each(function () {
    $(this).data("original-text", $(this).html())
  })

  // Dynamic field type handling in form builder
  $("#id_field_type").on("change", function () {
    var fieldType = $(this).val()
    var $optionsGroup = $(".field-options-group")
    var $validationGroup = $(".field-validation-group")

    // Show/hide options based on field type
    if (["select", "radio", "checkbox"].includes(fieldType)) {
      $optionsGroup.show()
    } else {
      $optionsGroup.hide()
    }

    // Show/hide validation options
    if (["text", "textarea", "email", "url", "phone"].includes(fieldType)) {
      $validationGroup.find(".length-validation").show()
    } else {
      $validationGroup.find(".length-validation").hide()
    }

    if (["number"].includes(fieldType)) {
      $validationGroup.find(".value-validation").show()
    } else {
      $validationGroup.find(".value-validation").hide()
    }
  })

  // Trigger field type change on page load
  $("#id_field_type").trigger("change")

  // Copy to clipboard functionality
  window.copyToClipboard = (text) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
        window.showToast("Copied to clipboard!", "success")
      })
    } else {
      // Fallback for older browsers
      var textArea = document.createElement("textarea")
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand("copy")
      document.body.removeChild(textArea)
      window.showToast("Copied to clipboard!", "success")
    }
  }

  // Toast notification system
  window.showToast = (message, type, duration) => {
    type = type || "info"
    duration = duration || 3000

    var alertClass = "alert-" + (type === "error" ? "danger" : type)
    var iconClass =
      {
        success: "fas fa-check-circle",
        error: "fas fa-exclamation-circle",
        warning: "fas fa-exclamation-triangle",
        info: "fas fa-info-circle",
      }[type] || "fas fa-info-circle"

    var toast = $(`
            <div class="alert ${alertClass} alert-dismissible fade show position-fixed" 
                 style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
                <i class="${iconClass} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `)

    $("body").append(toast)

    setTimeout(() => {
      toast.alert("close")
    }, duration)
  }

  // Smooth scrolling for anchor links
  $('a[href^="#"]').on("click", function (e) {
    e.preventDefault()
    var target = $($(this).attr("href"))
    if (target.length) {
      $("html, body").animate(
        {
          scrollTop: target.offset().top - 100,
        },
        500,
      )
    }
  })

  // Auto-resize textareas
  $("textarea")
    .each(function () {
      this.setAttribute("style", "height:" + this.scrollHeight + "px;overflow-y:hidden;")
    })
    .on("input", function () {
      this.style.height = "auto"
      this.style.height = this.scrollHeight + "px"
    })

  // Enhanced form field interactions
  $(".form-control, .form-select")
    .on("focus", function () {
      $(this).closest(".field-group").addClass("focused")
    })
    .on("blur", function () {
      $(this).closest(".field-group").removeClass("focused")
    })

  // Character counter for text fields with max length
  $("input[maxlength], textarea[maxlength]").each(function () {
    var $field = $(this)
    var maxLength = $field.attr("maxlength")
    var $counter = $('<small class="text-muted character-counter"></small>')
    $field.after($counter)

    function updateCounter() {
      var remaining = maxLength - $field.val().length
      $counter.text(remaining + " characters remaining")

      if (remaining < 10) {
        $counter.addClass("text-warning")
      } else {
        $counter.removeClass("text-warning")
      }
    }

    $field.on("input", updateCounter)
    updateCounter()
  })
})

// Utility functions
function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")
}

function debounce(func, wait, immediate) {
  var timeout
  return function () {
    var args = arguments
    var later = () => {
      timeout = null
      if (!immediate) func.apply(this, args)
    }
    var callNow = immediate && !timeout
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
    if (callNow) func.apply(this, args)
  }
}

// Export functions for global use
window.FormBuilder = {
  showToast: window.showToast,
  copyToClipboard: window.copyToClipboard,
  formatNumber: formatNumber,
  debounce: debounce,
}
