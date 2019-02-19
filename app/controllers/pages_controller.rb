class PagesController < ApplicationController

  def index
    @postings = current_user.postings.order(created_at: :desc) if user_signed_in?
  end
end
