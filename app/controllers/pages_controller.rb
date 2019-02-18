class PagesController < ApplicationController

  def index
    @postings = current_user.postings if user_signed_in?
  end
end
